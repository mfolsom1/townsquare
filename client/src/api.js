// api.js: Backend API helpers

// Base URL for the backend API
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:5000';

/**
 * A generic helper function to streamline API requests.
 * It handles the fetch call, JSON parsing, authentication headers, and error handling.
 * @param {string} url - The API endpoint to call.
 * @param {object} options - The options object for the fetch call (e.g., method, body).
 * @param {string|null} idToken - The Firebase ID token for authenticated requests.
 * @returns {Promise<any>} The JSON data from the API response.
 * @throws {Error} If the API response is not ok.
 */
async function apiRequest(url, options = {}, idToken = null) {
    const headers = {
        "Content-Type": "application/json",
        ...options.headers,
    };

    // Add the Authorization header if an ID token is provided
    if (idToken) {
        headers["Authorization"] = `Bearer ${idToken}`;
    }

    const config = {
        ...options,
        headers,
    };

    // Prepend the base URL to the endpoint
    const fullUrl = `${API_BASE_URL}${url}`;
    const response = await fetch(fullUrl, config);
    const data = await response.json();

    if (!response.ok) {
        // Throw an error with the message from the backend, or a default message
        throw new Error(data.error || `Request failed with status ${response.status}`);
    }

    return data;
}

//============================================
// ===== Authentication & User Profile =====
//============================================

/**
 * Verifies the Firebase ID token with the backend.
 * This will create a new user in the database if one doesn't already exist.
 * @param {string} idToken - The user's Firebase ID token.
 * @param {object} userData - Additional user data for account creation (username, name, etc.).
 * @returns {Promise<object>} The user data from the backend.
 */
export async function verifyUserWithBackend(idToken, userData = {}) {
    return apiRequest("/api/auth/verify", {
        method: "POST",
        body: JSON.stringify({ idToken, userData }),
    });
}

/**
 * Fetches the current user's profile from the backend.
 * @param {string} idToken - The user's Firebase ID token for authentication.
 * @returns {Promise<object>} The user's profile data.
 */
export async function getUserProfile(idToken) {
    return apiRequest("/api/user/profile", { method: "GET" }, idToken);
}

/**
 * Updates the current user's profile.
 * @param {string} idToken - The user's Firebase ID token for authentication.
 * @param {object} profileData - An object with the fields to update (e.g., { username, location, bio }).
 * @returns {Promise<object>} The updated user profile data.
 */
export async function updateUserProfile(idToken, profileData) {
    return apiRequest("/api/user/profile", {
        method: "PUT",
        body: JSON.stringify(profileData),
    }, idToken);
}

//================================
// ===== Interest Management =====
//================================

/**
 * Fetches the current user's interests.
 * @param {string} idToken - The user's Firebase ID token for authentication.
 * @returns {Promise<Array<string>>} A list of the user's interests.
 */
export async function getUserInterests(idToken) {
    return apiRequest("/api/user/interests", { method: "GET" }, idToken);
}

/**
 * Adds a single interest to the user's profile.
 * @param {string} idToken - The user's Firebase ID token for authentication.
 * @param {string} interestName - The name of the interest to add.
 * @returns {Promise<object>} The updated list of user interests.
 */
export async function addUserInterest(idToken, interestName) {
    return apiRequest("/api/user/interests", {
        method: "POST",
        body: JSON.stringify({ interest: interestName }),
    }, idToken);
}

/**
 * Removes a single interest from the user's profile.
 * @param {string} idToken - The user's Firebase ID token for authentication.
 * @param {string} interestName - The name of the interest to remove.
 * @returns {Promise<object>} The updated list of user interests.
 */
export async function removeUserInterest(idToken, interestName) {
    return apiRequest("/api/user/interests", {
        method: "DELETE",
        body: JSON.stringify({ interest: interestName }),
    }, idToken);
}

/**
 * Sets all user interests at once (replaces existing interests).
 * This is a convenience function that uses the profile update endpoint.
 * @param {string} idToken - The user's Firebase ID token for authentication.
 * @param {Array<string>} interests - An array of interest names to set as the user's interests.
 * @returns {Promise<object>} The updated user profile data.
 */
export async function setUserInterests(idToken, interests) {
    return apiRequest("/api/user/profile", {
        method: "PUT",
        body: JSON.stringify({ interests }),
    }, idToken);
}

/**
 * Fetches all available interests in the system.
 * This endpoint doesn't require authentication.
 * @returns {Promise<Array<object>>} A list of all available interests with their names and descriptions.
 */
export async function getAllInterests() {
    return apiRequest("/api/interests", { method: "GET" });
}

//===========================
// ===== Event Actions =====
//===========================

/**
 * Fetches a list of filtered events or all events from the backend.
 * @param {object} filters - Optional filters to apply (e.g., {q: 'search term'}).
 * @param {object} options - Optional settings (e.g., pagination).
 * @returns {Promise<object>} Object containing events array and pagination info.
 */
export async function getEvents(filters = {}, options = {}) {
    const params = new URLSearchParams();

    Object.entries(filters).forEach(([k, v]) => {
        if (v == null) return;
        if (Array.isArray(v)) {
            v.forEach(item => params.append(k, item));
        }
        else {
            params.append(k, String(v));
        }
    });

    const qs = params.toString();
    const url = `/events${qs ? `?${qs}` : ''}`;

    return apiRequest(url, { method: "GET", ...options });
}

/**
 * Fetches a single event by its unique ID.
 * @param {number} eventId - The ID of the event to retrieve.
 * @returns {Promise<object>} The event data.
 */
export async function getEventById(eventId) {
    return apiRequest(`/events/${eventId}`, { method: "GET" });
}

/**
 * Creates a new event.
 * @param {string} idToken - The user's Firebase ID token for authentication.
 * @param {object} eventData - The data for the new event (e.g., { Title, StartTime, Location, ... }).
 * @returns {Promise<object>} The newly created event data.
 */
export async function createEvent(idToken, eventData) {
    return apiRequest("/events", {
        method: "POST",
        body: JSON.stringify(eventData),
    }, idToken);
}

/**
 * Updates an existing event's details.
 * @param {string} idToken - The user's Firebase ID token for authentication.
 * @param {number} eventId - The ID of the event to update.
 * @param {object} updateData - An object containing the event fields to update.
 * @returns {Promise<object>} The updated event data.
 */
export async function updateEvent(idToken, eventId, updateData) {
    return apiRequest(`/events/${eventId}`, {
        method: "PATCH",
        body: JSON.stringify(updateData),
    }, idToken);
}

/**
 * Deletes an event.
 * @param {string} idToken - The user's Firebase ID token for authentication.
 * @param {number} eventId - The ID of the event to delete.
 * @returns {Promise<object>} A success confirmation message.
 */
export async function deleteEvent(idToken, eventId) {
    return apiRequest(`/events/${eventId}`, {
        method: "DELETE",
    }, idToken);
}

/**
 * Fetches events organized by the current user.
 * @param {string} idToken - The user's Firebase ID token for authentication.
 * @returns {Promise<Array<object>>} A list of events organized by the user.
 */
export async function getUserOrganizedEvents(idToken) {
    return apiRequest("/api/user/events/organized", { method: "GET" }, idToken);
}

/**
 * Fetches events the current user is attending.
 * @param {string} idToken - The user's Firebase ID token for authentication.
 * @returns {Promise<Array<object>>} A list of events the user is attending.
 */
export async function getUserAttendingEvents(idToken) {
    return apiRequest("/api/user/events/attending", { method: "GET" }, idToken);
}

/**
 * Creates or updates an RSVP for an event.
 * @param {string} idToken - The user's Firebase ID token for authentication.
 * @param {number} eventId - The ID of the event to RSVP to.
 * @param {string} status - The RSVP status ('Going', 'Interested', 'Not Going').
 * @returns {Promise<object>} The created/updated RSVP data.
 */
export async function createOrUpdateRsvp(idToken, eventId, status = 'Going') {
    return apiRequest(`/api/events/${eventId}/rsvp`, {
        method: "POST",
        body: JSON.stringify({ status }),
    }, idToken);
}

/**
 * Deletes an RSVP for an event.
 * @param {string} idToken - The user's Firebase ID token for authentication.
 * @param {number} eventId - The ID of the event to remove RSVP from.
 * @returns {Promise<object>} A success confirmation message.
 */
export async function deleteRsvp(idToken, eventId) {
    return apiRequest(`/api/events/${eventId}/rsvp`, {
        method: "DELETE",
    }, idToken);
}

/**
 * Fetches all RSVPs for the current user.
 * @param {string} idToken - The user's Firebase ID token for authentication.
 * @returns {Promise<Array<object>>} A list of the user's RSVPs.
 */
export async function getUserRsvps(idToken) {
    return apiRequest("/api/user/rsvps", { method: "GET" }, idToken);
}

//===========================
// ===== Friend Events =====
//===========================

/**
 * Fetches events that the user's friends are attending or interested in.
 * @param {string} idToken - The Firebase ID token for authentication.
 * @returns {Promise<Array<object>>} A list of friend-RSVP'd events.
 */
export async function getFriendRsvps(idToken) {
    return apiRequest("/api/friends/rsvps", { method: "GET" }, idToken);
}

/**
 * Fetches events that were created by the user's friends.
 * @param {string} idToken - The Firebase ID token for authentication.
 * @returns {Promise<Array<object>>} A list of events created by friends.
 */
export async function getFriendCreatedEvents(idToken) {
    return apiRequest("/api/friends/created", { method: "GET" }, idToken);
}

/**
 * Fetches the full friend feed (both attended/interested and created events).
 * @param {string} idToken - The Firebase ID token for authentication.
 * @returns {Promise<Array<object>>} A combined list of friend feed events.
 */
export async function getFriendFeed(idToken) {
    return apiRequest("/api/friends/feed", { method: "GET" }, idToken);
}


//===============================
// ===== Recommendations =====
//===============================

/**
 * Fetches personalized event recommendations for the authenticated user.
 * @param {string} idToken - The user's Firebase ID token for authentication.
 * @param {number} topK - Number of recommendations to fetch (default 10, max 50).
 * @param {string} strategy - Recommendation strategy ('hybrid', 'friends_only', 'friends_boosted').
 * @returns {Promise<object>} Object containing recommendations array and metadata.
 */
export async function getRecommendations(idToken, topK = 10, strategy = 'hybrid') {
    const params = new URLSearchParams();
    params.append('top_k', topK);
    params.append('strategy', strategy);

    return apiRequest(`/api/recommendations?${params.toString()}`, {
        method: "GET"
    }, idToken);
}

//===============================
// ===== Social Functions =====
//===============================

/**
 * Follow a user by their Firebase UID or username.
 * @param {string} idToken - The user's Firebase ID token for authentication.
 * @param {string} targetUid - The Firebase UID of the user to follow.
 * @param {string} targetUsername - The username of the user to follow (alternative to targetUid).
 * @returns {Promise<object>} Success confirmation.
 */
export async function followUser(idToken, targetUid = null, targetUsername = null) {
    const body = {};
    if (targetUid) body.firebase_uid = targetUid;
    if (targetUsername) body.username = targetUsername;

    return apiRequest("/api/social/follow", {
        method: "POST",
        body: JSON.stringify(body),
    }, idToken);
}

/**
 * Unfollow a user by their Firebase UID or username.
 * @param {string} idToken - The user's Firebase ID token for authentication.
 * @param {string} targetUid - The Firebase UID of the user to unfollow.
 * @param {string} targetUsername - The username of the user to unfollow (alternative to targetUid).
 * @returns {Promise<object>} Success confirmation.
 */
export async function unfollowUser(idToken, targetUid = null, targetUsername = null) {
    const body = {};
    if (targetUid) body.firebase_uid = targetUid;
    if (targetUsername) body.username = targetUsername;

    return apiRequest("/api/social/unfollow", {
        method: "POST",
        body: JSON.stringify(body),
    });
}

/**
 * Get the list of users the current user is following.
 * @param {string} idToken - The user's Firebase ID token for authentication.
 * @returns {Promise<object>} Object containing following list and count.
 */
export async function getFollowing(idToken) {
    return apiRequest("/api/social/following", {
        method: "GET"
    }, idToken);
}

/**
 * Get the list of users following the current user.
 * @param {string} idToken - The user's Firebase ID token for authentication.
 * @returns {Promise<object>} Object containing followers list and count.
 */
export async function getFollowers(idToken) {
    return apiRequest("/api/social/followers", {
        method: "GET"
    }, idToken);
}

/**
 * Get public user information by Firebase UID.
 * @param {string} firebaseUid - The Firebase UID of the user.
 * @returns {Promise<object>} Object containing public user information.
 */
export async function getUserPublicInfo(firebaseUid) {
    return apiRequest(`/api/user/${firebaseUid}/public`, {
        method: "GET"
    });
}

/**
 * Check if the current user is following another user.
 * @param {string} idToken - The user's Firebase ID token for authentication.
 * @param {string} targetUid - The Firebase UID of the target user.
 * @returns {Promise<object>} Object containing is_following boolean.
 */
export async function checkFollowingStatus(idToken, targetUid) {
    return apiRequest(`/api/social/following/${targetUid}`, {
        method: "GET"
    }, idToken);
}

//===============================
// ===== Organizations =========
//===============================

/**
 * Fetch a single organization by ID.
 * Requires auth because membership / permissions are checked on the backend.
 * @param {string} idToken - Firebase ID token
 * @param {number|string} orgId - Organization ID
 */
export async function getOrganization(idToken, orgId) {
    return apiRequest(`/api/organizations/${orgId}`, { method: "GET" }, idToken);
}

/**
 * Update an organization.
 * Backend route (from routes.py) allows fields like 'name' and 'description'.
 * @param {string} idToken - Firebase ID token
 * @param {number|string} orgId - Organization ID
 * @param {object} data - Fields to update (e.g. { name, description })
 */
export async function updateOrganization(idToken, orgId, data) {
    return apiRequest(`/api/organizations/${orgId}`, {
        method: "PUT",
        body: JSON.stringify(data),
    }, idToken);
}

// ===============================
// ===== Organization metrics ====
// ===============================

/**
 * Fetch RSVPs per day for the current org for the last 30 days.
 * @param {string} idToken - Firebase ID token for auth
 * @returns {Promise<{success: boolean, total: number, timeseries: Array<{date:string,count:number}>}>}
 */
export async function getOrgRsvpsLast30(idToken) {
    return apiRequest("/api/org/metrics/rsvps/30days", { method: "GET" }, idToken);
}

/**
 * Fetch new followers per day for the current org for the last 30 days.
 * @param {string} idToken - Firebase ID token for auth
 * @returns {Promise<{success: boolean, total: number, timeseries: Array<{date:string,count:number}>}>}
 */
export async function getOrgFollowersLast30(idToken) {
    return apiRequest("/api/org/metrics/followers/30days", { method: "GET" }, idToken);
}
