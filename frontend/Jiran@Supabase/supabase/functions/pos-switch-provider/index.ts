import { serve } from "https://deno.land/std/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const SUPABASE_URL = Deno.env.get("SUPABASE_URL")!;
const SERVICE_ROLE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers":
    "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};

serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  const authHeader = req.headers.get("Authorization");
  if (!authHeader) {
    return new Response(
      JSON.stringify({ error: "Missing Authorization header" }),
      { status: 401, headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );
  }

  try {
    const supabase = createClient(SUPABASE_URL, SERVICE_ROLE_KEY);
    const { retailer_id, target_provider, connection_id } = await req.json();

    if (!retailer_id || !target_provider) {
      return new Response(
        JSON.stringify({ error: "Missing retailer_id or target_provider" }),
        { status: 400, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    if (!["manual", "square"].includes(target_provider)) {
      return new Response(
        JSON.stringify({ error: "Invalid provider" }),
        { status: 400, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    const now = new Date().toISOString();

    const { data: allConnections, error: loadErr } = await supabase
      .from("pos_connections")
      .select("id, provider")
      .eq("retailer_id", retailer_id);

    if (loadErr) {
      return new Response(
        JSON.stringify({ error: loadErr.message }),
        { status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    let activeConnectionId: string | null = null;

    // =====================================================
    // SWITCH TO MANUAL
    // =====================================================
    if (target_provider === "manual") {
      // 🔴 Deactivate ALL Square-backed data
      await supabase
        .from("products")
        .update({ active: false, updated_at: now })
        .eq("retailer_id", retailer_id)
        .not("pos_connection_id", "is", null);

      await supabase
        .from("product_variations")
        .update({ active: false, updated_at: now })
        .not("pos_connection_id", "is", null);

      await supabase
        .from("orders")
        .update({ is_active: false, updated_at: now })
        .eq("retailer_id", retailer_id)
        .not("pos_connection_id", "is", null);

      await supabase
        .from("order_items")
        .update({ is_active: false, updated_at: now })
        .not("pos_connection_id", "is", null);

      // 🚫 DO NOT reactivate old manual rows
      // New manual inserts will automatically be active

      const manualConn = allConnections?.find((c) => c.provider === "manual");

      if (manualConn) {
        activeConnectionId = manualConn.id;

        await supabase
          .from("pos_connections")
          .update({ status: "connected", last_error: null, updated_at: now })
          .eq("id", manualConn.id);
      } else {
        const { data: created, error: createErr } = await supabase
          .from("pos_connections")
          .insert({
            retailer_id,
            provider: "manual",
            consumer_id: retailer_id,
            status: "connected",
            is_active: false,
            created_at: now,
            updated_at: now,
          })
          .select("id")
          .single();

        if (createErr || !created) {
          return new Response(
            JSON.stringify({ error: createErr?.message || "Failed to create manual connection" }),
            { status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" } }
          );
        }

        activeConnectionId = created.id;
      }
    }

    // =====================================================
    // SWITCH TO SQUARE
    // =====================================================
    if (target_provider === "square") {
      if (!connection_id) {
        return new Response(
          JSON.stringify({ error: "Missing connection_id for square activation" }),
          { status: 400, headers: { ...corsHeaders, "Content-Type": "application/json" } }
        );
      }

      // 🔴 Deactivate ALL manual data
      await supabase
        .from("products")
        .update({ active: false, updated_at: now })
        .eq("retailer_id", retailer_id)
        .is("pos_connection_id", null);

      await supabase
        .from("product_variations")
        .update({ active: false, updated_at: now })
        .is("pos_connection_id", null);

      await supabase
        .from("orders")
        .update({ is_active: false, updated_at: now })
        .eq("retailer_id", retailer_id)
        .is("pos_connection_id", null);

      await supabase
        .from("order_items")
        .update({ is_active: false, updated_at: now })
        .is("pos_connection_id", null);

      // 🟢 Activate ONLY this Square connection’s data
      await supabase
        .from("products")
        .update({ active: true, updated_at: now })
        .eq("retailer_id", retailer_id)
        .eq("pos_connection_id", connection_id);

      await supabase
        .from("product_variations")
        .update({ active: true, updated_at: now })
        .eq("pos_connection_id", connection_id);

      await supabase
        .from("orders")
        .update({ is_active: true, updated_at: now })
        .eq("retailer_id", retailer_id)
        .eq("pos_connection_id", connection_id);

      await supabase
        .from("order_items")
        .update({ is_active: true, updated_at: now })
        .eq("pos_connection_id", connection_id);

      const squareConn = allConnections?.find(
        (c) => c.id === connection_id && c.provider === "square"
      );

      if (!squareConn) {
        return new Response(
          JSON.stringify({ error: "Square connection not found for retailer" }),
          { status: 404, headers: { ...corsHeaders, "Content-Type": "application/json" } }
        );
      }

      activeConnectionId = squareConn.id;

      await supabase
        .from("pos_connections")
        .update({ status: "connected", last_error: null, updated_at: now })
        .eq("id", squareConn.id);
    }

    if (!activeConnectionId) {
      return new Response(
        JSON.stringify({ error: "Failed to resolve active connection" }),
        { status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    // =====================================================
    // ENSURE ONLY ONE ACTIVE CONNECTION
    // =====================================================
    await supabase
      .from("pos_connections")
      .update({ is_active: false, updated_at: now })
      .eq("retailer_id", retailer_id);

    await supabase
      .from("pos_connections")
      .update({ is_active: true, updated_at: now })
      .eq("id", activeConnectionId)
      .eq("retailer_id", retailer_id);

    return new Response(
      JSON.stringify({
        success: true,
        active_connection_id: activeConnectionId,
        provider: target_provider,
      }),
      { status: 200, headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );
  } catch (err: any) {
    return new Response(
      JSON.stringify({ error: err.message }),
      { status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );
  }
});