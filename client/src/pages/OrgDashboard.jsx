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
  getFollowers,
  getOrgRsvpsLast30,
  getOrgFollowersLast30,
} from "../api.js";

const FALLBACK_ORG = {
  name: "Umbrella Corp",
  handle: "@umbrella",
  location: "Gainesville, FL",
  email: "email@example.com",
  followers: 10,
  bannerUrl: "https://www.google.com/url?sa=i&url=https%3A%2F%2Fdesignbundles.net%2Fladadikart%2F2893326-umbrellas-in-hands-banner-rainy-day-storm-and-hand&psig=AOvVaw07DHeE7a-r6GSWYf3Mo78O&ust=1763036993943946000&source=images&cd=vfe&opi=89978449&ved=0CBYQjRxqFwoTCNDxv-XO7JADFQAAAAAdAAAAABAE=format&fit=crop",
  avatarUrl: null,
  about: "Welcome to Umbrella Corporations.",
  tags: ["Arts", "Music", "Tech", "Food & Drink"],
};

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
  // initialize from fallback + any initial props (do not store reference to FALLBACK_ORG)
  const [org, setOrg] = useState(() => ({
    ...FALLBACK_ORG,
    ...(initialOrg || {}),
  }));
  const [events, setEvents] = useState(propsEvents || []);

  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
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
    nav("/login", { replace: true });
  };

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

        // fetch profile and organized events in a simple, robust way
        const raw = await getUserProfile(idToken);
        const profile = raw && raw.user ? raw.user : raw || {};
        const followers = await getFollowers(idToken);
        const followerCount = followers ? followers.count : 0;

        // derive a display name and stable defaults
        const nameFromProfile =
          profile.organization_name ||
          [profile.first_name, profile.last_name]
            .filter(Boolean)
            .join(" ")
            .trim() ||
          profile.name ||
          profile.displayName ||
          profile.username ||
          FALLBACK_ORG.name;

        const mapped = {
          name: nameFromProfile,
          handle: profile.username || FALLBACK_ORG.handle,
          location: profile.location || FALLBACK_ORG.location,
          email: profile.email || FALLBACK_ORG.email,
          followers: followerCount,
          bannerUrl:
            profile.bannerUrl || FALLBACK_ORG.bannerUrl,
          avatarUrl:
            profile.avatarUrl || FALLBACK_ORG.avatarUrl,
          about:
            profile.about ||
            profile.description ||
            profile.bio ||
            FALLBACK_ORG.about,
          tags: Array.isArray(profile.tags)
            ? profile.tags
            : profile.interests || FALLBACK_ORG.tags,
        };

        if (!alive) return;
        setOrg((prev) => ({ ...prev, ...mapped }));

        // organized events (keep existing formatter)
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
      } catch (e) {
        const msg = String(e?.message || "").toLowerCase();
        if (msg.includes("user not found") || msg.includes("404")) {
          try {
            const idToken = user ? await user.getIdToken() : null;
            if (idToken) {
              await verifyUserWithBackend(idToken, {
                username: (user?.email || "user").split("@")[0],
                name: user?.displayName || FALLBACK_ORG.name,
                email: user?.email || "",
              });
              // retry once
              if (!alive) return;
              const idToken2 = await user.getIdToken();
              const raw2 = await getUserProfile(idToken2);
              const profile2 = raw2 && raw2.user ? raw2.user : raw2 || {};
              const nameFromProfile2 =
                profile2.organization_name ||
                [profile2.first_name, profile2.last_name]
                  .filter(Boolean)
                  .join(" ")
                  .trim() ||
                profile2.name ||
                profile2.displayName ||
                profile2.username ||
                FALLBACK_ORG.name;
              setOrg((prev) => ({ ...prev, name: nameFromProfile2 }));
            }
          } catch (inner) {
            if (!alive) return;
            setError(inner?.message || "Failed to verify user");
          }
        } else {
          if (!alive) return;
          setError(e?.message || "Failed to load organization dashboard");
        }
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

  // handle save: merge optimistic UI update and persist
  const handleSaveProfile = async (payload) => {
    // optimistic merge
    setOrg((prev) => ({ ...prev, ...payload }));
    try {
      if (typeof onSaveOrgProfile === "function") {
        const saved = await onSaveOrgProfile(payload);
        // if API returns updated profile, merge that too
        if (saved && typeof saved === "object") {
          setOrg((prev) => ({ ...prev, ...saved }));
        }
      }
    } catch (e) {
      console.error("Failed to save organization profile:", e);
      // optionally refetch to recover authoritative state
    }
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

            <button
              className="org-logout-btn"
              type="button"
              onClick={handleLogout}
            >
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
