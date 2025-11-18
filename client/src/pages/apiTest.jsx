import React, { useEffect } from "react";
import { getAuth } from "firebase/auth";
import { getFriendRsvps, getFriendCreatedEvents, getFriendFeed, getUserInterests, setUserInterests, getAllInterests } from "../api"; // adjust path

export default function ApiTest() {
  useEffect(() => {
    const fetchFriendData = async () => {
      const auth = getAuth();
      const user = auth.currentUser;

      if (!user) {
        console.log("No user signed in.");
        return;
      }

      try {
        const idToken = await user.getIdToken();

        const friendEvents = await getFriendRsvps(idToken);
        console.log("Friend Events:", friendEvents);

        const friendCreated = await getFriendCreatedEvents(idToken);
        console.log("Friend Created Events:", friendCreated);

        const friendFeed = await getFriendFeed(idToken);
        console.log("Friend Feed:", friendFeed);

        const allInterests = await getAllInterests();
        console.log("All Interests (public):", allInterests);

        const currentInterests = await getUserInterests(idToken);
        console.log("Current Interests:", currentInterests);

        const afterSet = await setUserInterests(idToken, [
          "Art",
          "Music",
          "Networking",
        ]);
        console.log("After Setting All Interests:", afterSet);
        
        const currentInterests2 = await getUserInterests(idToken);
        console.log("Current Interests:", currentInterests2);

      } catch (error) {
        console.error("Error fetching friend data:", error);
      }
    };

    fetchFriendData();
  }, []);

  return (
    <main style={{ padding: "2rem" }}>
      <h1>Testing Friend APIs</h1>
      <p>Check the console for results of the API calls.</p>
    </main>
  );
}
