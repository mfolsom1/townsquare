import { 
    getUserInterests, 
    addUserInterest, 
    removeUserInterest, 
    setUserInterests, 
    getAllInterests 
} from './api.js';

async function testInterestAPIs() {
    // Mock Firebase ID token for testing
    const idToken = "HCDOopDtExNCQowPqByfLou3VsI2";
    
    try {
        console.log("=== Testing Interest Management APIs ===\n");

        // Test 1: Get all available interests
        console.log("1. Getting all available interests...");
        try {
            const allInterests = await getAllInterests();
            console.log("✓ All interests:", allInterests);
        } catch (error) {
            console.log("✗ Error getting all interests:", error.message);
        }

        // Test 2: Get user's current interests
        console.log("\n2. Getting user's current interests...");
        try {
            const userInterests = await getUserInterests(idToken);
            console.log("✓ User interests:", userInterests);
        } catch (error) {
            console.log("✗ Error getting user interests:", error.message);
        }

        // Test 3: Add a single interest
        console.log("\n3. Adding interest 'Photography'...");
        try {
            const addResult = await addUserInterest(idToken, "Photography");
            console.log("✓ Interest added:", addResult);
        } catch (error) {
            console.log("✗ Error adding interest:", error.message);
        }

        // Test 4: Remove a single interest
        console.log("\n4. Removing interest 'Photography'...");
        try {
            const removeResult = await removeUserInterest(idToken, "Photography");
            console.log("✓ Interest removed:", removeResult);
        } catch (error) {
            console.log("✗ Error removing interest:", error.message);
        }

        // Test 5: Set all interests at once
        console.log("\n5. Setting interests to ['Technology', 'Sports', 'Music']...");
        try {
            const setResult = await setUserInterests(idToken, ["Technology", "Sports", "Music"]);
            console.log("✓ Interests set:", setResult);
        } catch (error) {
            console.log("✗ Error setting interests:", error.message);
        }

        console.log("\n=== Test completed ===");
        
    } catch (error) {
        console.error("General test error:", error);
    }
}

// Run the test
testInterestAPIs();