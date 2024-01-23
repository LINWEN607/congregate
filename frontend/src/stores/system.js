import { defineStore } from "pinia"

export const useSystemStore = defineStore('system', {
    state: () => ({
        settings: {},
        listingInProgress: false,
        migrationInProgress: false
    }),
    actions: {
        updateSettings(settings) {
            this.settings = settings
        },
        updateListingInProgress(state) {
            this.listingInProgress = state
        },
        updateMigrationInProgress(state) {
            this.migrationInProgress = state
        }
    }
})
