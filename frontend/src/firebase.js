import { initializeApp } from 'firebase/app'
import { getFirestore, collection, addDoc, getDocs, query, orderBy, limit, doc, deleteDoc } from 'firebase/firestore'

// Firebase configuration from environment variables
const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
  measurementId: import.meta.env.VITE_FIREBASE_MEASUREMENT_ID
}

// Debug: Log configuration (without sensitive data)
console.log('Firebase Config:', {
  hasApiKey: !!firebaseConfig.apiKey,
  hasProjectId: !!firebaseConfig.projectId,
  projectId: firebaseConfig.projectId
})

// Initialize Firebase
let app, db
try {
  app = initializeApp(firebaseConfig)
  db = getFirestore(app)
  console.log('Firebase initialized successfully')
} catch (error) {
  console.error('Firebase initialization failed:', error)
}

// History service
export const historyService = {
  // Save a new history entry
  async saveHistoryEntry(entry) {
    console.log('Attempting to save history entry:', { 
      hasCode: !!entry.code, 
      hasResult: !!entry.result, 
      hasTestResult: !!entry.testResult 
    })
    
    try {
      if (!db) {
        throw new Error('Firestore not initialized')
      }
      
      const historyData = {
        ...entry,
        timestamp: new Date(),
        createdAt: new Date()
      }
      
      console.log('Saving to Firestore with data:', historyData)
      const docRef = await addDoc(collection(db, 'history'), historyData)
      console.log('Document saved successfully with ID:', docRef.id)
      return { success: true, id: docRef.id }
    } catch (error) {
      console.error('Error saving history to Firestore:', error)
      console.error('Error details:', {
        code: error.code,
        message: error.message,
        stack: error.stack
      })
      return { success: false, error: error.message, details: error.code }
    }
  },

  // Get all history entries
  async getHistory() {
    console.log('Attempting to fetch history from Firestore')
    
    try {
      if (!db) {
        throw new Error('Firestore not initialized')
      }
      
      const q = query(collection(db, 'history'), orderBy('timestamp', 'desc'), limit(100))
      console.log('Executing query:', q)
      
      const querySnapshot = await getDocs(q)
      console.log('Query completed, found documents:', querySnapshot.size)
      
      const history = []
      querySnapshot.forEach((doc) => {
        history.push({ id: doc.id, ...doc.data() })
      })
      
      console.log('History fetched successfully:', history.length, 'entries')
      return { success: true, data: history }
    } catch (error) {
      console.error('Error getting history from Firestore:', error)
      console.error('Error details:', {
        code: error.code,
        message: error.message,
        stack: error.stack
      })
      return { success: false, error: error.message, data: [] }
    }
  },

  // Delete a history entry
  async deleteHistoryEntry(id) {
    console.log('Attempting to delete history entry:', id)
    
    try {
      if (!db) {
        throw new Error('Firestore not initialized')
      }
      
      await deleteDoc(doc(db, 'history', id))
      console.log('Document deleted successfully:', id)
      return { success: true }
    } catch (error) {
      console.error('Error deleting history:', error)
      return { success: false, error: error.message }
    }
  },

  // Clear all history
  async clearAllHistory() {
    console.log('Attempting to clear all history')
    
    try {
      if (!db) {
        throw new Error('Firestore not initialized')
      }
      
      const q = query(collection(db, 'history'))
      const querySnapshot = await getDocs(q)
      
      console.log('Found documents to delete:', querySnapshot.size)
      
      const deletePromises = []
      querySnapshot.forEach((doc) => {
        deletePromises.push(deleteDoc(doc.ref))
      })
      
      await Promise.all(deletePromises)
      console.log('All documents deleted successfully')
      return { success: true }
    } catch (error) {
      console.error('Error clearing history:', error)
      return { success: false, error: error.message }
    }
  }
}

export default db
