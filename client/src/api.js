// api.js: Backend API helpers

// Verify user with backend using Firebase ID token
export async function verifyUserWithBackend(idToken) {
	const response = await fetch("/api/auth/verify", {
		method: "POST",
		headers: {
			"Content-Type": "application/json",
		},
		body: JSON.stringify({ idToken }),
	});
	const data = await response.json();
	if (!response.ok) {
		throw new Error(data.error || "Failed to verify user with backend");
	}
	return data;
}