/**
 * IndexedDB Storage Manager for AI Data Cleaner
 * Stores cleaned datasets locally in the browser
 */

const DB_NAME = 'ai-data-cleaner';
const DB_VERSION = 1;
const STORE_NAME = 'cleaned-datasets';

class StorageManager {
    constructor() {
        this.db = null;
    }

    /**
     * Initialize the IndexedDB database
     */
    async init() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open(DB_NAME, DB_VERSION);

            request.onerror = () => {
                console.error('Database failed to open');
                reject(request.error);
            };

            request.onsuccess = () => {
                this.db = request.result;
                console.log('✓ Database initialized successfully');
                resolve(this.db);
            };

            request.onupgradeneeded = (event) => {
                const db = event.target.result;

                // Create object store if it doesn't exist
                if (!db.objectStoreNames.contains(STORE_NAME)) {
                    const objectStore = db.createObjectStore(STORE_NAME, {
                        keyPath: 'id',
                        autoIncrement: true
                    });

                    // Create indexes for querying
                    objectStore.createIndex('timestamp', 'timestamp', { unique: false });
                    objectStore.createIndex('filename', 'filename', { unique: false });

                    console.log('✓ Object store created');
                }
            };
        });
    }

    /**
     * Save cleaned dataset to IndexedDB
     * @param {Object} data - Dataset information
     * @returns {Promise<number>} - The ID of the saved dataset
     */
    async saveDataset(data) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([STORE_NAME], 'readwrite');
            const objectStore = transaction.objectStore(STORE_NAME);

            const datasetRecord = {
                filename: data.filename,
                originalFilename: data.originalFilename || data.filename,
                userPrompt: data.userPrompt,
                rules: data.rules,
                parserUsed: data.parserUsed,
                actionsLog: data.actionsLog,
                stats: data.stats,
                cleanedData: data.cleanedData, // Store the actual CSV data
                columnNames: data.columnNames,
                timestamp: new Date().toISOString()
            };

            const request = objectStore.add(datasetRecord);

            request.onsuccess = () => {
                console.log('✓ Dataset saved with ID:', request.result);
                resolve(request.result);
            };

            request.onerror = () => {
                console.error('Failed to save dataset');
                reject(request.error);
            };
        });
    }

    /**
     * Get all saved datasets (for history view)
     * @returns {Promise<Array>} - Array of dataset records
     */
    async getAllDatasets() {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([STORE_NAME], 'readonly');
            const objectStore = transaction.objectStore(STORE_NAME);
            const request = objectStore.getAll();

            request.onsuccess = () => {
                // Sort by timestamp descending (newest first)
                const datasets = request.result.sort((a, b) =>
                    new Date(b.timestamp) - new Date(a.timestamp)
                );
                resolve(datasets);
            };

            request.onerror = () => {
                console.error('Failed to retrieve datasets');
                reject(request.error);
            };
        });
    }

    /**
     * Get a specific dataset by ID
     * @param {number} id - Dataset ID
     * @returns {Promise<Object>} - Dataset record
     */
    async getDataset(id) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([STORE_NAME], 'readonly');
            const objectStore = transaction.objectStore(STORE_NAME);
            const request = objectStore.get(id);

            request.onsuccess = () => {
                resolve(request.result);
            };

            request.onerror = () => {
                console.error('Failed to retrieve dataset');
                reject(request.error);
            };
        });
    }

    /**
     * Delete a dataset by ID
     * @param {number} id - Dataset ID
     * @returns {Promise<void>}
     */
    async deleteDataset(id) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([STORE_NAME], 'readwrite');
            const objectStore = transaction.objectStore(STORE_NAME);
            const request = objectStore.delete(id);

            request.onsuccess = () => {
                console.log('✓ Dataset deleted:', id);
                resolve();
            };

            request.onerror = () => {
                console.error('Failed to delete dataset');
                reject(request.error);
            };
        });
    }

    /**
     * Clear all datasets (for testing or reset)
     * @returns {Promise<void>}
     */
    async clearAll() {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([STORE_NAME], 'readwrite');
            const objectStore = transaction.objectStore(STORE_NAME);
            const request = objectStore.clear();

            request.onsuccess = () => {
                console.log('✓ All datasets cleared');
                resolve();
            };

            request.onerror = () => {
                console.error('Failed to clear datasets');
                reject(request.error);
            };
        });
    }

    /**
     * Get storage statistics
     * @returns {Promise<Object>} - Storage info
     */
    async getStorageInfo() {
        const datasets = await this.getAllDatasets();
        const totalSize = JSON.stringify(datasets).length;

        return {
            count: datasets.length,
            sizeBytes: totalSize,
            sizeMB: (totalSize / (1024 * 1024)).toFixed(2)
        };
    }
}

// Create a global instance
const storage = new StorageManager();

// Initialize on page load
window.addEventListener('DOMContentLoaded', async () => {
    try {
        await storage.init();
    } catch (error) {
        console.error('Failed to initialize storage:', error);
        showToast('Storage initialization failed', 'error');
    }
});
