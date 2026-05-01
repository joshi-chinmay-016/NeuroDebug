// Firebase Test Utility
import { historyService } from './firebase.js'

export async function testFirebaseConnection() {
  console.log('=== Firebase Connection Test ===')
  
  // Test 1: Check environment variables
  console.log('1. Checking environment variables...')
  const envVars = {
    apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
    projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
    authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
    appId: import.meta.env.VITE_FIREBASE_APP_ID
  }
  
  const missingVars = Object.entries(envVars)
    .filter(([key, value]) => !value)
    .map(([key]) => key)
  
  if (missingVars.length > 0) {
    console.error('❌ Missing environment variables:', missingVars)
    return { success: false, error: 'Missing environment variables', missing: missingVars }
  }
  
  console.log('✅ All environment variables present')
  console.log('Project ID:', envVars.projectId)
  
  // Test 2: Try to save a test document
  console.log('2. Testing write operation...')
  try {
    const testEntry = {
      code: 'print("test")',
      result: { error_type: 'test_error', explanation: 'This is a test' },
      testResult: null,
      test: true
    }
    
    const saveResult = await historyService.saveHistoryEntry(testEntry)
    
    if (!saveResult.success) {
      console.error('❌ Write operation failed:', saveResult.error)
      
      // Check for common Firebase errors
      if (saveResult.details === 'permission-denied') {
        console.error('🔥 Firestore Rules Issue: Database is not set to allow writes')
        console.error('Solution: Update Firestore security rules to allow read/write access')
        console.error('Go to Firebase Console > Firestore Database > Rules and set:')
        console.error('rules_version = "2";')
        console.error('service cloud.firestore {')
        console.error('  match /databases/{database}/documents {')
        console.error('    match /{document=**} {')
        console.error('      allow read, write: if true;')
        console.error('    }')
        console.error('  }')
        console.error('}')
      } else if (saveResult.details === 'unavailable' || saveResult.details === 'not-found') {
        console.error('🔥 Firestore Database Issue: Database may not be created')
        console.error('Solution: Go to Firebase Console and create a Firestore database')
      }
      
      return { success: false, error: saveResult.error, details: saveResult.details }
    }
    
    console.log('✅ Write operation successful, ID:', saveResult.id)
    
    // Test 3: Try to read the test document
    console.log('3. Testing read operation...')
    const readResult = await historyService.getHistory()
    
    if (!readResult.success) {
      console.error('❌ Read operation failed:', readResult.error)
      return { success: false, error: readResult.error, details: readResult.details }
    }
    
    console.log('✅ Read operation successful, found:', readResult.data.length, 'documents')
    
    // Test 4: Clean up test document
    if (saveResult.id) {
      console.log('4. Cleaning up test document...')
      const deleteResult = await historyService.deleteHistoryEntry(saveResult.id)
      if (deleteResult.success) {
        console.log('✅ Test document cleaned up')
      } else {
        console.warn('⚠️ Could not clean up test document:', deleteResult.error)
      }
    }
    
    console.log('=== All Firebase Tests Passed ===')
    return { success: true, message: 'Firebase connection working properly' }
    
  } catch (error) {
    console.error('❌ Unexpected error during test:', error)
    return { success: false, error: error.message, stack: error.stack }
  }
}

// Auto-run test in development
if (import.meta.env.DEV) {
  setTimeout(() => {
    testFirebaseConnection().then(result => {
      if (result.success) {
        console.log('🎉 Firebase is ready to use!')
      } else {
        console.error('💥 Firebase setup needs attention')
      }
    })
  }, 2000)
}
