// import { supabase } from "./Client.js";


// export const getMyProfile = async (userId) => {
//   return await supabase
//     .from("profiles")
//     .select("*")
//     .eq("id", userId)
//     .single();
// };

import { supabase } from "./Client.js";

export const getMyProfile = async (userId) => {
  return await supabase
    .from("profiles")
    .select("*")
    .eq("id", userId)
    .maybeSingle();
};

