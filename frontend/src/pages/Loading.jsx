import React, { useEffect, useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { supabase } from "../supaBase/Client";
import { useAuth } from "../context/AuthContext";
import "../styles/Loading.css";


const Loading = () => {
    const startedAtRef = useRef(new Date().toISOString());
  const navigate = useNavigate();
  const { user } = useAuth();

  const [message, setMessage] = useState("Connecting to Square...");
  const [dots, setDots] = useState("");

  // animated dots
  useEffect(() => {
    const interval = setInterval(() => {
      setDots((d) => (d.length >= 3 ? "" : d + "."));
    }, 500);

    return () => clearInterval(interval);
  }, []);

  // start POS sync when loading page opens
  useEffect(() => {
    if (!user) return;

    const startSync = async () => {
      try {
        await supabase.functions.invoke("pos-sync", {
          body: { retailer_id: user.id },
        });
      } catch (err) {
        console.error("Failed to start pos-sync:", err);
        setMessage("Sync failed. Please reconnect your POS.");
      }
    };

    startSync();
  }, [user]);

  // poll sync status
  useEffect(() => {
    if (!user) return;

    const checkSync = async () => {
      const { data, error } = await supabase
        .from("pos_connections")
        .select("last_synced_at, last_error")
        .eq("retailer_id", user.id)
        .eq("is_active", true)
        .single();

      if (error) return;

      if (data?.last_synced_at && data.last_synced_at >= startedAtRef.current) {
        navigate("/inventory");
        return;
      }

      if (data?.last_error) {
        setMessage("Sync failed. Please reconnect your POS.");
      }
    };

    const interval = setInterval(checkSync, 3000);

    return () => clearInterval(interval);
  }, [user, navigate]);

  return (
    <div className="loading-page">
      <div className="loading-card">
        <div className="spinner" />

        <h1>Syncing Your Inventory</h1>

        <p className="loading-message">
          {message}
          {dots}
        </p>

        <p className="loading-sub">
          This usually takes a few seconds while we import your products and
          inventory levels.
        </p>

        <div className="progress-bar">
          <div className="progress-fill" />
        </div>
      </div>
    </div>
  );
};

export default Loading;
