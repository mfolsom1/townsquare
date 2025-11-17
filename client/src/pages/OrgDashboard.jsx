import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import "./OrgDashboard.css";
import CreateEvent from "../components/CreateEvent";
import OrgEditProfile from "../components/OrgEditProfile";
import {
  getUserProfile,
  getUserOrganizedEvents,
  verifyUserWithBackend,
  getOrgRsvpsLast30,
  getOrgFollowersLast30,
} from "../api.js";

const initialsFromName = (name = "Organization") =>
  name
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((p) => p[0]?.toUpperCase())
    .join("") || "O";

export default function OrgDashboard({
  events: propsEvents = [],
  onCreateEvent,
  onSaveOrgProfile,
  initialOrg,
}) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // org state is seeded from container fallback but will be replaced by backend data
  const fallbackOrg = initialOrg || {
    name: "Umbrella Corp",
    handle: "@umbrella",
    location: "Gainesville, FL",
    email: "email@example.com",
    followers: 8,
    bannerUrl:
      "https://www.google.com/url?sa=i&url=https%3A%2F%2Fdesignbundles.net%2Fladadikart%2F2893326-umbrellas-in-hands-banner-rainy-day-storm-and-hand&psig=AOvVaw07DHeE7a-r6GSWYf3Mo78O&ust=1763036993943946000&source=images&cd=vfe&opi=89978449&ved=0CBYQjRxqFwoTCNDxv-XO7JADFQAAAAAdAAAAABAE=format&fit=crop",
    avatarUrl: null,
    about: "Welcome to Umbrella Corporations.",
    tags: ["Arts", "Music", "Tech", "Food & Drink"],
  };
  
  const [org, setOrg] = useState(null);
  const [events, setEvents] = useState(propsEvents);
  const [analyticsRsvps, setAnalyticsRsvps] = useState([]); // { date, count }
  const [analyticsFollowers, setAnalyticsFollowers] = useState([]);
  const [selectedAnalytics, setSelectedAnalytics] = useState("rsvps"); // "rsvps" | "followers"
  const [analyticsLoading, setAnalyticsLoading] = useState(true);
  

  // helper to normalize event objects for this dashboard UI
  const formatEventForUI = (event) => ({
    title: event.title || event.name || "Untitled",
    date: event.start_time
      ? new Date(event.start_time).toLocaleDateString()
      : "TBD",
    location: event.location || "",
    id: event.event_id ?? event.id,
    imageUrl: event.image_url ?? event.imageUrl ?? null,
  });

  const nav = useNavigate();
  const handleLogout = async () => {
    await logout();
    nav("/login", { replace: true })
  }

  // Load authenticated user's org profile and organized events (same pattern as ProfileContainer)
  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        if (!user) {
          navigate("/login", { replace: true });
          return;
        }
        setLoading(true);
        const idToken = await user.getIdToken();

        const load = async () => {
          const rawProfile = await getUserProfile(idToken);
          // attempt to map backend fields to org UI shape
          const profile = rawProfile || {};
          console.log(rawProfile)
          const orgData = {
            name:
              profile.name ||
              profile.organization_name ||
              profile.displayName ||
              fallbackOrg.name,
            handle: profile.handle || profile.username || fallbackOrg.handle,
            location: profile.location || fallbackOrg.location,
            email: profile.email || fallbackOrg.email,
            followers: profile.followers ?? fallbackOrg.followers,
            bannerUrl:
              profile.bannerUrl || profile.banner_url || fallbackOrg.bannerUrl,
            avatarUrl:
              profile.avatarUrl || profile.avatar_url || fallbackOrg.avatarUrl,
            about: profile.about || profile.description || fallbackOrg.about,
            tags: Array.isArray(profile.tags) ? profile.tags : fallbackOrg.tags,
          };
          if (!alive) return;
          setOrg((prev) => ({ ...prev, ...orgData }));

          // load organized events
          try {
            const res = await getUserOrganizedEvents(idToken);
            const organized = res?.events || [];
            if (!alive) return;
            setEvents(organized.map(formatEventForUI));
          } catch (e) {
            console.warn("Failed to fetch organized events:", e);
            if (!alive) return;
            setEvents([]);
          }
        };

        try {
          await load();
        } catch (e) {
          const msg = String(e?.message || "").toLowerCase();
          if (msg.includes("user not found") || msg.includes("404")) {
            // create/verify backend user and retry (same flow as ProfileContainer)
            await verifyUserWithBackend(idToken, {
              username: (user?.email || "user").split("@")[0],
              name: user?.displayName || "New Organization",
              email: user?.email || "",
            });
            if (!alive) return;
            await load();
          } else {
            throw e;
          }
        }
      } catch (e) {
        if (!alive) return;
        setError(e?.message || "Failed to load organization dashboard");
      } finally {
        if (!alive) return;
        setLoading(false);
      }
    })();

    return () => {
      alive = false;
    };
  }, [user, navigate]);

  // helper to build last-30-days array of date keys YYYY-MM-DD
  const lastNDates = (n = 30) => {
    const out = [];
    const today = new Date();
    for (let i = n - 1; i >= 0; i--) {
      const d = new Date(today);
      d.setDate(today.getDate() - i + 1);
      const yyyy = d.getFullYear();
      const mm = String(d.getMonth() + 1).padStart(2, "0");
      const dd = String(d.getDate()).padStart(2, "0");
      out.push(`${yyyy}-${mm}-${dd}`);
    }
    return out;
  };

  const formatLabel = (iso) => {
    const d = new Date(iso);
    return `${d.getMonth() + 1}/${d.getDate()}`;
  };

  useEffect(() => {
    let alive = true;
    (async () => {
      if (!user) return;
      try {
        setAnalyticsLoading(true);
        const idToken = await user.getIdToken();

        const [rsvpsRes, follRes] = await Promise.allSettled([
          getOrgRsvpsLast30(idToken),
          getOrgFollowersLast30(idToken),
        ]);

        if (!alive) return;

        const days = lastNDates(30);
        const toSeries = (res) => {
          if (!res || !res.value || !res.value.timeseries)
            return days.map((d) => ({ date: d, count: 0 }));
          const map = new Map(
            res.value.timeseries.map((p) => [p.date, Number(p.count) || 0])
          );
          return days.map((d) => ({ date: d, count: map.get(d) || 0 }));
        };

        setAnalyticsRsvps(toSeries(rsvpsRes));
        setAnalyticsFollowers(toSeries(follRes));
      } catch (e) {
        console.warn("Failed to load analytics:", e);
      } finally {
        if (alive) setAnalyticsLoading(false);
      }
    })();
    return () => {
      alive = false;
    };
  }, [user]);

  // compute series to render based on selection
  const activeSeries =
    selectedAnalytics === "rsvps" ? analyticsRsvps : analyticsFollowers;
  const maxVal = Math.max(1, ...activeSeries.map((s) => s.count));

  const initials = initialsFromName(org.name);

  // Create Event Modal
  const [isCreateOpen, setCreateOpen] = useState(false);
  const openCreate = () => setCreateOpen(true);
  const closeCreate = () => setCreateOpen(false);

  const handleCreate = (data) => {
    if (typeof onCreateEvent === "function") {
      onCreateEvent(data);
    }
    // optimistically add to list (optional)
    setEvents((prev) => [formatEventForUI(data), ...(prev || [])]);
    console.log("New event created:", data);
  };

  // Edit Profile Modal
  const [isEditOpen, setEditOpen] = useState(false);
  const openEdit = () => setEditOpen(true);
  const closeEdit = () => setEditOpen(false);

  const handleSaveProfile = async (payload) => {
    // update UI immediately
    setOrg((prev) => ({
      ...prev,
      name: payload.name ?? prev.name,
      email: payload.email ?? prev.email,
      location: payload.location ?? prev.location,
      about: payload.about ?? prev.about,
      tags: Array.isArray(payload.tags) ? payload.tags : prev.tags,
    }));

    // persist via callback if provided
    try {
      if (typeof onSaveOrgProfile === "function") {
        await onSaveOrgProfile(payload);
      }
    } catch (e) {
      console.error("Failed to save organization profile:", e);
    }

    return payload;
  };

  if (loading) return <div style={{ padding: 16 }}>Loading dashboard…</div>;
  if (error)
    return <div style={{ padding: 16, color: "#b91c1c" }}>Error: {error}</div>;

  return (
    <div className="org-page">
      <div className="org-hero">
        <img
          className="org-banner"
          src={org.bannerUrl}
          alt="Organization banner"
        />
        {org.avatarUrl ? (
          <img
            className="org-avatar"
            src={org.avatarUrl}
            alt={`${org.name} logo`}
          />
        ) : (
          <div
            className="org-avatar org-avatar-initials"
            aria-label={`${org.name} initials`}
          >
            <span>{initials}</span>
          </div>
        )}
      </div>

      <div className="org-content">
        <aside className="org-sidebar">
          <div className="org-card">
            <div className="org-identity">
              <div className="org-name">{org.name}</div>
              <div className="org-handle">{org.handle}</div>
            </div>

            <div className="org-meta">
              <div className="org-meta-row">
                <span className="material-symbols-outlined">location_on</span>
                <span>{org.location}</span>
              </div>
              <div className="org-meta-row">
                <span className="material-symbols-outlined">mail</span>
                <a href={`mailto:${org.email}`}>{org.email}</a>
              </div>
              <div className="org-meta-row">
                <span className="material-symbols-outlined">group</span>
                <span>
                  <strong>{org.followers}</strong> Followers
                </span>
              </div>
            </div>

            <button className="org-edit-btn" type="button" onClick={openEdit}>
              Edit Profile
            </button>

            <div className="org-section">
              <div className="org-section-title">About</div>
              <p className="org-about">{org.about}</p>
            </div>

            <div className="org-section">
              <div className="org-section-title">Tags</div>
              <div className="org-tags">
                {org.tags.map((t) => (
                  <span className="org-tag" key={t}>
                    {t}
                  </span>
                ))}
              </div>
            </div>

            <button className="org-logout-btn" type="button" onClick={handleLogout}>
              Logout
            </button>
          </div>
        </aside>

        <main className="org-main">
          <div className="org-card org-events">
            <div className="org-events-header">
              <div className="org-events-title">Events</div>
              <button
                className="org-events-cta"
                type="button"
                onClick={openCreate}
              >
                Create Event
              </button>
            </div>

            {events.length ? (
              <div className="org-events-grid">
                {events.map((e) => (
                  <div key={e.id} className="org-event">
                    <div className="org-event-thumb">
                      {e.imageUrl ? (
                        <img src={e.imageUrl} alt={e.title} />
                      ) : (
                        <div className="org-event-thumb-placeholder">
                          <span className="material-symbols-outlined">
                            event
                          </span>
                        </div>
                      )}
                    </div>
                    <div className="org-event-body">
                      <div className="org-event-title">{e.title}</div>
                      <div className="org-event-sub">
                        {e.date} • {e.location}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="org-events-empty">No events yet.</div>
            )}
          </div>

          <div className="org-events-footer"></div>

          <section className="org-card org-analytics">
            <div className="org-analytics-header">
              <div>
                <div className="org-analytics-title">Analytics</div>
                <div className="org-analytics-sub">Last 30 days</div>
              </div>
            </div>

            <div className="org-analytics-tabs">
              <button
                className={`org-analytics-tab ${
                  selectedAnalytics === "rsvps"
                    ? "org-analytics-tab--active"
                    : ""
                }`}
                onClick={() => setSelectedAnalytics("rsvps")}
              >
                RSVP's
              </button>
              <button
                className={`org-analytics-tab ${
                  selectedAnalytics === "followers"
                    ? "org-analytics-tab--active"
                    : ""
                }`}
                onClick={() => setSelectedAnalytics("followers")}
              >
                New Followers
              </button>
            </div>

            <div className="org-analytics-chart">
              <div className="org-analytics-ylabel">
                {selectedAnalytics === "rsvps" ? "RSVPs" : "Followers"}
              </div>

              {analyticsLoading ? (
                <div style={{ padding: 12 }}>Loading chart…</div>
              ) : (
                <div className="org-analytics-bars">
                  {activeSeries.map((pt) => {
                    const h = Math.round((pt.count / maxVal) * 120); // scale to max 120px
                    return (
                      <div
                        key={pt.date}
                        className="org-analytics-bar-group"
                        title={`${formatLabel(pt.date)}: ${pt.count}`}
                      >
                        <div
                          className="org-analytics-bar"
                          style={{ height: `${h}px` }}
                        />
                        <div className="org-analytics-xlabel">
                          {formatLabel(pt.date)}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </section>
        </main>
      </div>

      <CreateEvent
        open={isCreateOpen}
        onClose={closeCreate}
        onCreate={handleCreate}
      />

      <OrgEditProfile
        open={isEditOpen}
        onClose={closeEdit}
        initial={{
          name: org.name,
          email: org.email,
          location: org.location,
          about: org.about,
          tags: org.tags,
        }}
        onSave={handleSaveProfile}
      />
    </div>
  );
}
