// firebase.js: Firebase config and auth setup

import { initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";
// TODO: Add other Firebase services as needed
// import { getFirestore } from "firebase/firestore";

// Your web app's Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyABDJ0e6AZpXqgTMJci017R-yMq6v0zDnI",
  authDomain: "townsquare-bee67.firebaseapp.com",
  projectId: "townsquare-bee67",
  storageBucket: "townsquare-bee67.firebasestorage.app",
  messagingSenderId: "329256581545",
  appId: "1:329256581545:web:d9e79d61753b1139782cb8"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);

// Initialize Firebase Authentication and get a reference to the service
export const auth = getAuth(app);

// Export the app for other Firebase services
export default app;