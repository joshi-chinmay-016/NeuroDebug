// DEPRECATED: Firebase has been migrated to PostgreSQL.
// This file is retained only for backward-compatibility stubs.
export const historyService = {
  saveHistoryEntry: async () => ({ success: false, error: 'Migrated to PostgreSQL' }),
  getHistory: async () => ({ success: true, data: [] }),
  deleteHistoryEntry: async () => ({ success: true })
};
