import React, { useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { supabase } from "../supaBase/Client.js";

// import "../styles/RetailDashboard.css";
import "../styles/Settings.css";
import Logo from "/src/styles/Logo.png";
import Avatar from "/src/styles/avatar.png"; 

/* ===============================
  Topbar
================================ */
function Topbar({ displayName, role, onLogout, activePage }) {
  return (
    <header className="topbar">
      <a
        href="/"
        className="brand brand-link"
        // target="_blank"
        rel="noopener noreferrer"
        aria-label="Go to landing page"
      >
        <img src={Logo} alt="Jiran Logo" className="nav-logo" />
        <div className="brand-text">
          <h1>Jiran</h1>
          <p>Retailer Dashboard</p>
        </div>
      </a>

      <nav className="nav" aria-label="Primary navigation">
        <Link
          className={`nav-item ${activePage === "dashboard" ? "active" : ""}`}
          to="/retailer-dashboard"
        >
          Dashboard
        </Link>
        <Link
          className={`nav-item ${activePage === "inventory" ? "active" : ""}`}
          to="/inventory"
        >
          Inventory
        </Link>
        <Link
          className={`nav-item ${activePage === "exchange" ? "active" : ""}`}
          to="/exchange"
        >
          Marketplace
        </Link>
        <Link
          className={`nav-item ${activePage === "analytics" ? "active" : ""}`}
          to="/analytics"
        >
          Analytics
        </Link>
        <Link
          className={`nav-item ${activePage === "settings" ? "active" : ""}`}
          to="/settings"
        >
          Settings
        </Link>
      </nav>

      <div className="top-actions">
        <button className="account" type="button">
          <span className="avatar">
            <img src={Avatar} alt="avatar" />
          </span>{" "}
          <span className="acct-text">
            <span className="acct-name">{displayName}</span>
            <span className="acct-sub">{role}</span>
          </span>
        </button>

        <button className="btn ghost small" onClick={onLogout}>
          Logout
        </button>
      </div>
    </header>
  );
}

const Panel = ({ children }) => <section className="panel">{children}</section>;

const Toggle = ({ title, active, color, onChange }) => {
  const cardStyle = {
    backgroundColor: active ? `${color}15` : "#f8fafc",
    border: `1px solid ${active ? color : "#e2e8f0"}`,
    opacity: active ? 1 : 0.7,
    padding: "20px",
    borderRadius: "12px",
    cursor: "pointer",
    transition: "all 0.3s ease",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
  };

  return (
    <div style={cardStyle} onClick={onChange}>
      <div className="toggle-text">
        <div style={{ fontWeight: 700, color: active ? color : "#64748b" }}>
          {title}
        </div>
        <div style={{ fontSize: "0.75rem", color: "#94a3b8" }}>
          {active ? "Enabled" : "Disabled"}
        </div>
      </div>

      <div
        className={`custom-switch ${active ? "on" : ""}`}
        style={{
          width: "40px",
          height: "20px",
          borderRadius: "20px",
          backgroundColor: active ? color : "#cbd5e1",
          position: "relative",
          transition: "background 0.3s",
        }}
      >
        <div
          style={{
            position: "absolute",
            top: "2px",
            left: active ? "22px" : "2px",
            width: "16px",
            height: "16px",
            borderRadius: "50%",
            background: "white",
            transition: "all 0.2s ease",
          }}
        />
      </div>
    </div>
  );
};

/* ===============================
  Helpers
================================ */
function parseMapLink(link) {
  try {
    const trimmed = String(link || "").trim();
    if (!trimmed) return null;

    const url = new URL(trimmed);

    if (url.searchParams.has("q")) {
      const rawQ = url.searchParams.get("q") || "";
      const match = rawQ.match(/(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)/);
      if (match) return { lat: Number(match[1]), lng: Number(match[2]) };
    }

    const pathMatch = url.pathname.match(
      /@(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)/,
    );
    if (pathMatch)
      return { lat: Number(pathMatch[1]), lng: Number(pathMatch[2]) };

    return null;
  } catch {
    return null;
  }
}

function isFiniteCoordinate(value) {
  return Number.isFinite(Number(value));
}

function normalizeCoords(lat, lng) {
  return {
    lat: isFiniteCoordinate(lat) ? Number(lat) : null,
    lng: isFiniteCoordinate(lng) ? Number(lng) : null,
  };
}

function buildGoogleMapsLink(lat, lng) {
  return isFiniteCoordinate(lat) && isFiniteCoordinate(lng)
    ? `https://www.google.com/maps?q=${Number(lat)},${Number(lng)}`
    : "";
}

async function reverseGeocode(lat, lng) {
  try {
    const url = `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}`;
    const res = await fetch(url, { headers: { Accept: "application/json" } });
    if (!res.ok) return null;
    const data = await res.json();
    return data?.display_name || null;
  } catch {
    return null;
  }
}

function isStrongPassword(password) {
  return (
    password.length >= 10 &&
    /[A-Z]/.test(password) &&
    /\d/.test(password) &&
    /[^A-Za-z0-9]/.test(password)
  );
}

function FieldRow({ label, value, href }) {
  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "160px 1fr",
        gap: "0.75rem",
        alignItems: "start",
        padding: "0.9rem 0",
        borderBottom: "1px solid #eef2f7",
      }}
    >
      <div style={{ color: "#64748b", fontWeight: 600 }}>{label}</div>
      <div style={{ color: "#0f172a", minWidth: 0, wordBreak: "break-word" }}>
        {href && value ? (
          <a href={href} target="_blank" rel="noreferrer" className="nav-btn">
            {value}
          </a>
        ) : (
          value || <span style={{ color: "#94a3b8" }}>Not set</span>
        )}
      </div>
    </div>
  );
}

/* ===============================
  Modal: Contact + Retailer info
================================ */
/* ===============================
  Updated Modal: Contact + Retailer info
================================ */
function EditRetailerInfoModal({
  isOpen,
  onClose,
  onSave,
  saving,
  initialData,
}) {
  const [storeName, setStoreName] = useState("");
  const [phone, setPhone] = useState("");
  const [localError, setLocalError] = useState("");

  useEffect(() => {
    if (!isOpen) return;
    setStoreName(initialData?.shop_name || "");
    setPhone(initialData?.phone || "");
    setLocalError("");
  }, [isOpen, initialData]);

  if (!isOpen) return null;

  const handleSubmit = async () => {
    const nextPhone = phone.trim();
    setLocalError("");
    await onSave({ storeName, phone: nextPhone });
  };

  return (
    <div className="modal-overlay" style={{ zIndex: 9999 }}>
      {/* Increased width to 800px to match a wide dashboard feel */}
      <div
        className="modal-card"
        style={{ width: "min(800px, 95vw)", maxWidth: "800px" }}
      >
        <h3
          style={{
            marginBottom: "0.5rem",
            fontSize: "1.4rem",
            fontWeight: 700,
          }}
        >
          Edit contact info
        </h3>
        <p style={{ color: "#64748b", marginBottom: "2rem" }}>
          Update your primary contact details. Store name is locked.
        </p>

        <div className="form grid-2" style={{ gap: "2rem" }}>
          <div className="field">
            <label style={{ fontWeight: 700, color: "#475569" }}>
              Store name
            </label>
            <input
              className="input"
              value={storeName}
              readOnly
              disabled
              style={{
                backgroundColor: "#f8fafc",
                border: "1px solid #e2e8f0",
                color: "#94a3b8",
              }}
            />
          </div>

          <div className="field">
            <label style={{ fontWeight: 700, color: "#475569" }}>Phone</label>
            <input
              className="input"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              placeholder="+971 50 000 0000"
            />
          </div>

          <div className="field">
            <label style={{ fontWeight: 700, color: "#475569" }}>
              Contact email
            </label>
            <input
              className="input"
              value={initialData?.email || ""}
              readOnly
              disabled
              style={{
                backgroundColor: "#f8fafc",
                border: "1px solid #e2e8f0",
                color: "#94a3b8",
              }}
            />
          </div>

          <div className="field">
            <label style={{ fontWeight: 700, color: "#475569" }}>
              Store ID
            </label>
            <input
              className="input"
              value={initialData?.store_id || ""}
              readOnly
              disabled
              style={{
                backgroundColor: "#f8fafc",
                border: "1px solid #e2e8f0",
                color: "#94a3b8",
              }}
            />
          </div>
        </div>

        <div
          className="modal-actions"
          style={{ marginTop: "2.5rem", justifyContent: "flex-end" }}
        >
          <button className="btn ghost" onClick={onClose} disabled={saving}>
            Cancel
          </button>
          <button
            className="btn primary"
            onClick={handleSubmit}
            disabled={saving}
          >
            {saving ? "Saving..." : "Save changes"}
          </button>
        </div>
      </div>
    </div>
  );
}
/*==============================
  Modal: Location
================================ */
function EditLocationModal({ isOpen, onClose, onSave, saving, initialData }) {
  const [label, setLabel] = useState("");
  const [mapLink, setMapLink] = useState("");
  const [lat, setLat] = useState(null);
  const [lng, setLng] = useState(null);
  const [localError, setLocalError] = useState("");
  const [locating, setLocating] = useState(false);

  useEffect(() => {
    if (!isOpen) return;
    setLabel(initialData?.location_label || "");
    setMapLink(initialData?.map_link || "");
    setLat(initialData?.latitude ?? null);
    setLng(initialData?.longitude ?? null);
    setLocalError("");
    setLocating(false);
  }, [isOpen, initialData]);

  if (!isOpen) return null;

  const handleMapLinkChange = (value) => {
    setMapLink(value);
    const coords = parseMapLink(value);
    if (coords) {
      setLat(coords.lat);
      setLng(coords.lng);
      setLocalError("");
    }
  };

  const handleUseCurrentLocation = async () => {
    if (!navigator.geolocation) {
      setLocalError("Geolocation is not supported in this browser.");
      return;
    }

    setLocating(true);
    setLocalError("");

    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        const { latitude, longitude } = pos.coords;
        setLat(latitude);
        setLng(longitude);
        setMapLink(buildGoogleMapsLink(latitude, longitude));

        if (!String(label || "").trim()) {
          const displayName = await reverseGeocode(latitude, longitude);
          setLabel(
            displayName ||
              `Current Location (${latitude.toFixed(4)}, ${longitude.toFixed(4)})`,
          );
        }

        setLocating(false);
      },
      (error) => {
        setLocalError(`Could not get current location: ${error.message}`);
        setLocating(false);
      },
      { enableHighAccuracy: true, timeout: 10000 },
    );
  };

  const handleSubmit = async () => {
    const trimmedLabel = String(label || "").trim();
    const trimmedMapLink = String(mapLink || "").trim();
    const coords = normalizeCoords(lat, lng);

    if (!trimmedLabel) {
      setLocalError("Location name cannot be empty.");
      return;
    }

    if (trimmedMapLink && (coords.lat == null || coords.lng == null)) {
      const parsed = parseMapLink(trimmedMapLink);
      if (!parsed) {
        setLocalError(
          "Paste a standard Google Maps link like https://www.google.com/maps?q=25.1822,55.4021 or use the 📍 button.",
        );
        return;
      }

      setLat(parsed.lat);
      setLng(parsed.lng);
      await onSave({
        locationLabel: trimmedLabel,
        mapLink: trimmedMapLink,
        latitude: parsed.lat,
        longitude: parsed.lng,
      });
      return;
    }

    setLocalError("");
    await onSave({
      locationLabel: trimmedLabel,
      mapLink: trimmedMapLink,
      latitude: coords.lat,
      longitude: coords.lng,
    });
  };

  return (
    <div className="modal-overlay">
      <div className="modal-card" style={{ width: "min(720px, 92vw)" }}>
        <h3>Edit store location</h3>
        <p>Manage the location name, Google Maps link, and coordinates.</p>

        <div className="form" style={{ marginTop: "1rem" }}>
          <div className="field">
            <label>Location name</label>
            <input
              className="input"
              value={label}
              onChange={(e) => setLabel(e.target.value)}
              placeholder="e.g. Downtown Branch"
            />
          </div>

          <div className="field">
            <label>Map link</label>
            <div
              style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}
            >
              <input
                className="input"
                value={mapLink}
                onChange={(e) => handleMapLinkChange(e.target.value)}
                placeholder="https://www.google.com/maps?q=25.1822,55.4021"
                style={{ flexGrow: 1 }}
              />
              <button
                type="button"
                className="btn ghost small"
                onClick={handleUseCurrentLocation}
                disabled={saving || locating}
                title="Use current location"
              >
                {locating ? "..." : "📍"}
              </button>
            </div>
          </div>

          <div className="form grid-2">
            <div className="field">
              <label>Latitude</label>
              <input
                className="input"
                value={lat ?? ""}
                onChange={(e) => setLat(e.target.value)}
                placeholder="Latitude"
              />
            </div>

            <div className="field">
              <label>Longitude</label>
              <input
                className="input"
                value={lng ?? ""}
                onChange={(e) => setLng(e.target.value)}
                placeholder="Longitude"
              />
            </div>
          </div>

          <div
            style={{
              display: "flex",
              gap: "0.5rem",
              flexWrap: "wrap",
              marginTop: "0.25rem",
            }}
          >
            <span className="info-bubble">Shared during transactions</span>
            <span className="info-bubble">
              Map link updates coordinates automatically
            </span>
          </div>
        </div>

        {localError && <p className="save-msg">{localError}</p>}

        <div className="modal-actions">
          <button
            className="btn ghost"
            onClick={onClose}
            disabled={saving || locating}
          >
            Cancel
          </button>
          <button
            className="btn primary"
            onClick={handleSubmit}
            disabled={saving || locating}
          >
            {saving ? "Saving..." : "Save location"}
          </button>
        </div>
      </div>
    </div>
  );
}

/* ===============================
  Modal: Change password
================================ */
function ChangePasswordModal({ isOpen, onClose, onSave, saving }) {
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPass, setShowPass] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [localError, setLocalError] = useState("");

  useEffect(() => {
    if (!isOpen) return;
    setNewPassword("");
    setConfirmPassword("");
    setShowPass(false);
    setShowConfirm(false);
    setLocalError("");
  }, [isOpen]);

  if (!isOpen) return null;

  const checks = {
    length: newPassword.length >= 10,
    upper: /[A-Z]/.test(newPassword),
    number: /[0-9]/.test(newPassword),
    special: /[!@#$%^&*(),.?":{}|<>]/.test(newPassword),
    match: newPassword === confirmPassword && confirmPassword !== "",
  };

  const allValid = Object.values(checks).every(Boolean);

  const handleUpdate = () => {
    setLocalError("");
    if (!allValid) {
      setLocalError("Please ensure all security requirements are met.");
      return;
    }
    onSave({ newPassword });
  };

  const Rule = ({ validated, text }) => (
    <div className={`rule-item ${validated ? "rule-valid" : "rule-invalid"}`}>
      {validated ? "✅" : "○"} {text}
    </div>
  );

  return (
    <div className="modal-overlay" style={{ zIndex: 10000 }}>
      <div className="modal-card" style={{ maxWidth: "480px", width: "95%" }}>
        <h2
          style={{ fontSize: "1.5rem", fontWeight: 800, marginBottom: "8px" }}
        >
          Change password
        </h2>

        <div className="password-rules-container">
          <span
            style={{ fontWeight: 700, fontSize: "0.9rem", color: "#475569" }}
          >
            Security Rules:
          </span>
          <div
            className={`rule-item ${checks.length ? "rule-valid" : "rule-invalid"}`}
          >
            {checks.length ? "✅" : "○"} At least 10 characters
          </div>
          <div
            className={`rule-item ${checks.upper ? "rule-valid" : "rule-invalid"}`}
          >
            {checks.upper ? "✅" : "○"} At least 1 uppercase letter
          </div>
          <div
            className={`rule-item ${checks.number ? "rule-valid" : "rule-invalid"}`}
          >
            {checks.number ? "✅" : "○"} At least 1 number
          </div>
          <div
            className={`rule-item ${checks.special ? "rule-valid" : "rule-invalid"}`}
          >
            {checks.special ? "✅" : "○"} At least 1 special character
          </div>
          <div
            className={`rule-item ${checks.match ? "rule-valid" : "rule-invalid"}`}
          >
            {checks.match ? "✅" : "○"} Passwords must match
          </div>
        </div>

        <div className="form">
          <div className="field">
            <label>New Password</label>
            <div className="password-input-wrapper">
              <input
                className="input"
                type={showPass ? "text" : "password"}
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="Enter new password"
              />
              <button
                type="button"
                className="password-toggle-btn"
                onClick={() => setShowPass(!showPass)}
              >
                {showPass ? "🙈" : "👁️"}
              </button>
            </div>
          </div>

          <div className="field" style={{ marginTop: "16px" }}>
            <label>Confirm New Password</label>
            <div className="password-input-wrapper">
              <input
                className="input"
                type={showConfirm ? "text" : "password"}
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Confirm new password"
              />
              <button
                type="button"
                className="password-toggle-btn"
                onClick={() => setShowConfirm(!showConfirm)}
              >
                {showConfirm ? "🙈" : "👁️"}
              </button>
            </div>
          </div>
        </div>

        {localError && (
          <div className="validation-error-msg">⚠️ {localError}</div>
        )}

        <div
          className="modal-actions"
          style={{ justifyContent: "flex-end", marginTop: "32px" }}
        >
          <button className="btn ghost" onClick={onClose} disabled={saving}>
            Cancel
          </button>
          <button
            className="btn primary"
            onClick={handleUpdate}
            disabled={saving || !allValid}
          >
            {saving ? "Updating..." : "Update password"}
          </button>
        </div>
      </div>
    </div>
  );
}

const SETTINGS_SECTIONS = [
  {
    id: "profile",
    label: "Profile",
    color: "#2563EB",
    desc: "Store + contact",
    title: "Retailer & contact info",
    subtitle: "Basic retailer identity and primary contact details.",
  },
  {
    id: "location",
    label: "Location",
    color: "#2563EB",
    desc: "Maps + coordinates",
    title: "Location",
    subtitle: "Primary store location used across transactions.",
  },
  {
    id: "password",
    label: "Password",
    color: "#2563EB",
    desc: "Account security",
    title: "Change password",
    subtitle: "Update your password from a dedicated security section.",
  },
];

function SectionSwitcher({ activeSection, onChange }) {
  return (
    <div
      style={{
        display: "grid",
        /* This ensures they stay in 3 columns but stretch to fill the new width */
        gridTemplateColumns: "repeat(3, 1fr)",
        gap: "1.2rem" /* Increased gap for a cleaner look */,
        width: "100%",
      }}
    >
      {SETTINGS_SECTIONS.map((tab) => {
        const isActive = activeSection === tab.id;
        return (
          <button
            key={tab.id}
            type="button"
            onClick={() => onChange(tab.id)}
            style={{
              border: `1px solid ${isActive ? tab.color : "#e2e8f0"}`,
              background: isActive ? `${tab.color}15` : "#ffffff",
              borderRadius: "16px",
              padding: "16px 18px",
              textAlign: "left",
              cursor: "pointer",
              transition: "all 0.25s ease",
              boxShadow: isActive
                ? `0 10px 26px ${tab.color}18`
                : "0 4px 16px rgba(15, 23, 42, 0.04)",
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                gap: "0.5rem",
              }}
            >
              <div>
                <div
                  style={{
                    fontWeight: 700,
                    color: isActive ? tab.color : "#0f172a",
                  }}
                >
                  {tab.label}
                </div>
                <div
                  style={{
                    fontSize: "0.8rem",
                    color: "#64748b",
                    marginTop: "0.2rem",
                  }}
                >
                  {tab.desc}
                </div>
              </div>
              <div
                style={{
                  width: 12,
                  height: 12,
                  borderRadius: 999,
                  background: isActive ? tab.color : "#cbd5e1",
                  marginTop: 4,
                  flexShrink: 0,
                }}
              />
            </div>
          </button>
        );
      })}
    </div>
  );
}

export default function Settings() {
  const {
    user,
    profile,
    retailerProfile,
    signOut,
    loading: authLoading,
  } = useAuth();
  const navigate = useNavigate();

  const [storeName, setStoreName] = useState("");
  const [phone, setPhone] = useState("");
  const [locationId, setLocationId] = useState(null);
  const [locationLabel, setLocationLabel] = useState("");
  const [latitude, setLatitude] = useState(null);
  const [longitude, setLongitude] = useState(null);
  const [mapLink, setMapLink] = useState("");

  const [savingProfile, setSavingProfile] = useState(false);
  const [savingLocation, setSavingLocation] = useState(false);
  const [savingPassword, setSavingPassword] = useState(false);
  const [message, setMessage] = useState("");
  const [notifications, setNotifications] = useState(null);
  const [showOOSWarning, setShowOOSWarning] = useState(false);
  const [showRetailerModal, setShowRetailerModal] = useState(false);
  const [showLocationModal, setShowLocationModal] = useState(false);
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [activeSection, setActiveSection] = useState("profile");

  const displayName = useMemo(() => {
    return (
      profile?.full_name ||
      user?.user_metadata?.full_name ||
      user?.email ||
      "there"
    );
  }, [profile, user]);

  const role = profile?.role || "Retailer";

  useEffect(() => {
    if (!authLoading && !user) {
      navigate("/login", { replace: true });
    }
  }, [authLoading, user, navigate]);

  const handleLogout = async () => {
    await signOut();
    navigate("/login", { replace: true });
  };

  const loadLocation = async () => {
    if (!user?.id) return;

    const { data, error } = await supabase
      .from("retailer_locations")
      .select("id, location_label, latitude, longitude, map_link")
      .eq("retailer_id", user.id)
      .eq("is_primary", true)
      .maybeSingle();

    if (error) {
      console.warn("loadLocation error:", error.message);
      return;
    }

    setLocationId(data?.id ?? null);
    setLocationLabel(data?.location_label ?? "");
    setLatitude(data?.latitude ?? null);
    setLongitude(data?.longitude ?? null);
    setMapLink(data?.map_link ?? "");
  };

  useEffect(() => {
    if (!user?.id) return;

    setStoreName(retailerProfile?.shop_name || "");
    setPhone(profile?.phone || user?.user_metadata?.phone || "");
    loadLocation();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user?.id, retailerProfile?.shop_name, profile?.phone]);

  useEffect(() => {
    if (!user?.id) return;

    const fetchPrefs = async () => {
      const { data } = await supabase
        .from("retailer_profiles")
        .select(
          "low_stock_notifications, oos_notifications, show_top_products_widget",
        )
        .eq("id", user.id)
        .single();

      if (data) {
        setNotifications({
          lowStock: data.low_stock_notifications,
          oos: data.oos_notifications,
          bestsellers: data.show_top_products_widget,
        });
      } else {
        setNotifications({ lowStock: true, oos: true, bestsellers: false });
      }
    };

    fetchPrefs();
  }, [user?.id]);

  const saveRetailerInfo = async ({
    storeName: nextStoreName,
    phone: nextPhone,
  }) => {
    if (!user?.id) {
      setMessage("Not logged in.");
      return;
    }

    setSavingProfile(true);
    setMessage("");

    try {
      const { error: profileErr } = await supabase
        .from("profiles")
        .update({ phone: nextPhone || null })
        .eq("id", user.id);

      if (profileErr) throw profileErr;

      setStoreName(nextStoreName);
      setPhone(nextPhone || "");
      setShowRetailerModal(false);
      setMessage("Contact info saved ✅");
    } catch (err) {
      setMessage(err?.message || "Could not save contact info.");
    } finally {
      setSavingProfile(false);
    }
  };

  const saveLocation = async ({
    locationLabel: nextLabel,
    mapLink: nextMapLink,
    latitude: nextLat,
    longitude: nextLng,
  }) => {
    if (!user?.id) {
      setMessage("Not logged in.");
      return;
    }

    setSavingLocation(true);
    setMessage("");

    try {
      const coords = normalizeCoords(nextLat, nextLng);
      const trimmedMapLink = String(nextMapLink || "").trim();

      const payload = {
        location_label: String(nextLabel || "").trim(),
        latitude: coords.lat,
        longitude: coords.lng,
        map_link: trimmedMapLink || null,
      };

      if (locationId) {
        const { error } = await supabase
          .from("retailer_locations")
          .update(payload)
          .eq("id", locationId)
          .eq("retailer_id", user.id);

        if (error) throw error;
      } else {
        const { data, error } = await supabase
          .from("retailer_locations")
          .insert({
            retailer_id: user.id,
            ...payload,
            is_primary: true,
          })
          .select("id")
          .single();

        if (error) throw error;
        setLocationId(data?.id ?? null);
      }

      setLocationLabel(payload.location_label);
      setLatitude(payload.latitude);
      setLongitude(payload.longitude);
      setMapLink(payload.map_link || "");
      setShowLocationModal(false);
      setMessage("Location saved ✅");
    } catch (err) {
      setMessage(err?.message || "Could not save location.");
    } finally {
      setSavingLocation(false);
    }
  };

  const savePassword = async ({ newPassword }) => {
    if (!user?.id) {
      setMessage("Not logged in.");
      return;
    }

    setSavingPassword(true);
    setMessage("");

    try {
      const { error } = await supabase.auth.updateUser({
        password: newPassword,
      });
      if (error) throw error;

      setShowPasswordModal(false);
      window.alert("Password updated successfully.");
      setMessage("Password updated ✅");
    } catch (err) {
      setMessage(err?.message || "Could not update password.");
    } finally {
      setSavingPassword(false);
    }
  };

  const handleToggle = (type, currentVal) => {
    const newVal = !currentVal;

    // Intercept: If turning OFF Out-of-Stock alerts, show the modal instead of saving
    if (type === "oos" && newVal === false) {
      setShowOOSWarning(true);
      return; // Stop here; the modal's "Confirm" button will take over
    }

    // Otherwise, save directly to the DB
    updateNotificationInDB(type, newVal);
  };
  const updateNotificationInDB = async (type, value) => {
    try {
      // 1. Ensure these keys match what you pass in: handleToggle("oos", ...)
      const columnMap = {
        oos: "oos_notifications", // 'oos' must match the 'type' string
        lowStock: "low_stock_notifications", // If you pass 'low', this works
        bestsellers: "show_top_products_widget",
      };

      const dbColumnName = columnMap[type];

      // Safety check: If the lookup fails, stop here before calling Supabase
      if (!dbColumnName) {
        console.error(`Mapping failed. Type "${type}" not found in columnMap.`);
        return;
      }

      const { error } = await supabase
        .from("retailer_profiles") // The error log shows this is the correct table
        .update({ [dbColumnName]: value }) // This will now be e.g., { oos_notifications: false }
        .eq("id", user.id);

      if (error) throw error;

      // Update local state
      setNotifications((prev) => ({ ...prev, [type]: value }));

      if (type === "oos" && value === false) {
        setShowOOSWarning(false);
      }
    } catch (err) {
      console.error("Error updating preference:", err.message || err);
    }
  };

  const activeMeta =
    SETTINGS_SECTIONS.find((item) => item.id === activeSection) ||
    SETTINGS_SECTIONS[0];

  const renderActiveSection = () => {
    if (activeSection === "profile") {
      return (
        <div>
          <div className="panel-head">
            <div className="panel-title">
              <h3>{activeMeta.title}</h3>
              <p>{activeMeta.subtitle}</p>
            </div>
            <button
              className="btn ghost small"
              type="button"
              onClick={() => setShowRetailerModal(true)}
            >
              Edit
            </button>
          </div>

          <div
            style={{
              marginTop: "1rem",
              border: `1px solid ${activeMeta.color}22`,
              borderRadius: "18px",
              padding: "1.1rem 1.2rem",
              background: `${activeMeta.color}08`,
            }}
          >
            <FieldRow label="Store name" value={storeName} />
            <FieldRow
              label="Store ID"
              value={retailerProfile?.store_id || ""}
            />
            <FieldRow label="Contact email" value={user?.email || ""} />
            <FieldRow label="Phone" value={phone} />
          </div>
        </div>
      );
    }

    if (activeSection === "location") {
      return (
        <div>
          <div className="panel-head">
            <div className="panel-title">
              <h3>{activeMeta.title}</h3>
              <p>{activeMeta.subtitle}</p>
            </div>
            <button
              className="btn ghost small"
              type="button"
              onClick={() => setShowLocationModal(true)}
            >
              Edit
            </button>
          </div>

          <div
            style={{
              marginTop: "1rem",
              border: `1px solid ${activeMeta.color}22`,
              borderRadius: "18px",
              padding: "1.1rem 1.2rem",
              background: `${activeMeta.color}08`,
            }}
          >
            <FieldRow label="Location name" value={locationLabel} />
            <FieldRow
              label="Map link"
              value={mapLink || "Open map"}
              href={mapLink || null}
            />
            <FieldRow
              label="Latitude"
              value={latitude == null ? "" : String(latitude)}
            />
            <FieldRow
              label="Longitude"
              value={longitude == null ? "" : String(longitude)}
            />
          </div>
        </div>
      );
    }

    return (
      <div>
        <div className="panel-head">
          <div className="panel-title">
            <h3>{activeMeta.title}</h3>
            <p>{activeMeta.subtitle}</p>
          </div>
          <button
            className="btn ghost small"
            type="button"
            onClick={() => setShowPasswordModal(true)}
          >
            Change
          </button>
        </div>

        <div
          style={{
            marginTop: "1rem",
            border: `1px solid ${activeMeta.color}22`,
            borderRadius: "18px",
            padding: "1.1rem 1.2rem",
            background: `${activeMeta.color}08`,
          }}
        >
          <FieldRow label="Password" value="••••••••••••" />
          <div
            style={{ paddingTop: "0.9rem", color: "#475569", lineHeight: 1.55 }}
          >
            Use this section to update the password for your retailer account.
            Keep using the same password rules as signup:
            <strong>
              {" "}
              at least 10 characters, 1 uppercase letter, 1 number, and 1
              special character.
            </strong>
          </div>
        </div>
      </div>
    );
  };

  if (authLoading) {
    return (
      <main className="retail-page">
        <Topbar
          displayName={displayName}
          role={role}
          onLogout={handleLogout}
          activePage="settings"
        />
        <section className="dash-layout">
          <section className="settings-layout">
            <section className="settings-left">
              <Panel>
                <div className="panel-title">
                  <h2>Settings</h2>
                  <p>Loading your retailer settings...</p>
                </div>
              </Panel>
            </section>
          </section>
        </section>
      </main>
    );
  }

  return (
    <main className="retail-page">
      <Topbar
        displayName={displayName}
        role={role}
        onLogout={handleLogout}
        activePage="settings"
      />

      <section className="dash-layout">
        <section className="settings-layout">
          <section className="settings-left">
            <Panel>
              <div className="panel-title">
                <h2>Settings</h2>
                <p>
                  Use the switcher below to manage profile, location, and
                  password.
                </p>
              </div>

              {message && <p className="save-msg">{message}</p>}
            </Panel>

            <Panel>
              <div className="panel-head" style={{ marginBottom: "1rem" }}>
                <div className="panel-title">
                  <h3>Manage account sections</h3>
                  <p>
                    Switch between profile, location, and password from the top
                    cards.
                  </p>
                </div>
              </div>

              <SectionSwitcher
                activeSection={activeSection}
                onChange={setActiveSection}
              />

              <div style={{ marginTop: "1.25rem" }}>
                {renderActiveSection()}
              </div>
            </Panel>

            <Panel>
              <div className="settings-container">
                <div className="panel-head" style={{ marginBottom: "1rem" }}>
                  <div className="panel-title">
                    <h3>Notifications</h3>
                    <p>Choose which inventory alerts you want to receive.</p>
                  </div>
                </div>

                <section className="toggles-grid">
                  {!notifications ? (
                    <p>Loading preferences...</p>
                  ) : (
                    <>
                      <Toggle
                        title="Low Stock"
                        active={notifications.lowStock}
                        color="#f59e0b"
                        onChange={() =>
                          handleToggle("lowStock", notifications.lowStock)
                        }
                      />
                      <Toggle
                        title="Out of Stock"
                        active={notifications.oos}
                        color="#ef4444"
                        onChange={() => handleToggle("oos", notifications.oos)}
                      />
                      {/* New Bestsellers Toggle */}
                      <Toggle
                        title="Top 10 Bestsellers"
                        active={notifications.bestsellers}
                        color="#3b82f6"
                        onChange={() =>
                          handleToggle("bestsellers", notifications.bestsellers)
                        }
                      />
                    </>
                  )}
                </section>
              </div>
            </Panel>
          </section>
        </section>
      </section>

      <EditRetailerInfoModal
        isOpen={showRetailerModal}
        onClose={() => setShowRetailerModal(false)}
        onSave={saveRetailerInfo}
        saving={savingProfile}
        initialData={{
          shop_name: storeName,
          phone,
          email: user?.email || "",
          store_id: retailerProfile?.store_id || "",
        }}
      />

      <EditLocationModal
        isOpen={showLocationModal}
        onClose={() => setShowLocationModal(false)}
        onSave={saveLocation}
        saving={savingLocation}
        initialData={{
          location_label: locationLabel,
          map_link: mapLink,
          latitude,
          longitude,
        }}
      />

      <ChangePasswordModal
        isOpen={showPasswordModal}
        onClose={() => setShowPasswordModal(false)}
        onSave={savePassword}
        saving={savingPassword}
      />

      {showOOSWarning && (
        <div className="modal-overlay">
          <div className="modal-card">
            <h3>Disable critical alerts?</h3>
            <p>
              Turning off Out-of-Stock alerts might result in lost sales. Are
              you sure?
            </p>
            <div className="modal-actions">
              <button
                className="btn ghost"
                onClick={() => setShowOOSWarning(false)}
              >
                Cancel
              </button>
              <button
                className="btn-danger"
                onClick={() => updateNotificationInDB("oos", false)}
              >
                Confirm Disable
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
