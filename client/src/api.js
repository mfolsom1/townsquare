// api.js: Backend API helpers

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

    const response = await fetch(url, config);
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
 * @returns {Promise<object>} The user data from the backend.
 */
export async function verifyUserWithBackend(idToken) {
    return apiRequest("/api/auth/verify", {
        method: "POST",
        body: JSON.stringify({ idToken }),
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

//===========================
// ===== Event Actions =====
//===========================

/**
 * Fetches all events from the backend.
 * @returns {Promise<Array<object>>} A list of all events.
 */
export async function getAllEvents() {
    return apiRequest("/events", { method: "GET" });
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
    return apiRequest(`/events/${eventId}`, { method: "DELETE" }, idToken);
}

//===============================
// ===== Recommendations =====
//===============================

/**
 * Fetches event recommendations for a specific user.
 * @param {number} userId - The ID of the user for whom to get recommendations.
 * @returns {Promise<Array<object>>} A list of recommended events.
 */
export async function getRecommendations(userId) {
    return apiRequest(`/recommendations/${userId}`, { method: "GET" });
}

// build query string and call /events
function buildQueryString(params = {}) {
    const qs = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
        // skip null/undefined/empty
        if (v === undefined || v === null || v === '') return;
        // If value is an array, append each item (e.g. tags)
        if (Array.isArray(v)) {
            v.forEach(item => qs.append(k, String(item)));
        } else {
            qs.append(k, String(v));
        }
    });
    return qs.toString();
}

export async function getEvents(params = {}) {
    const qs = buildQueryString(params);
    const url = qs ? `/events?${qs}` : '/events';
    return apiRequest(url, { method: 'GET' });
}