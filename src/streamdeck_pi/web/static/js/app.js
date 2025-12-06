const { createApp } = Vue;

createApp({
    data() {
        return {
            deviceInfo: null,
            buttons: [],
            plugins: [],
            pages: [],
            currentPageId: null,
            brightness: 50,
            editingButton: null,
            newPageTitle: '',
            showPageModal: false
        };
    },
    computed: {
        pluginsByCategory() {
            const grouped = {};
            this.plugins.forEach(plugin => {
                const category = plugin.category || 'general';
                if (!grouped[category]) {
                    grouped[category] = [];
                }
                grouped[category].push(plugin);
            });
            return grouped;
        },
        selectedPluginInfo() {
            if (!this.editingButton || !this.editingButton.selectedPlugin) {
                return null;
            }
            return this.plugins.find(p => p.id === this.editingButton.selectedPlugin);
        }
    },
    methods: {
        async loadDeviceInfo() {
            try {
                const response = await axios.get('/api/v1/device');
                this.deviceInfo = response.data;
            } catch (error) {
                console.error('Failed to load device info:', error);
            }
        },
        async loadPages() {
            try {
                const response = await axios.get('/api/v1/pages');
                this.pages = response.data;
                // If we don't have a current page, assume the first one or fetch it?
                // The backend keeps track of current page.
                // But we don't know which one it is unless we ask.
                // Actually, loadButtons returns buttons for the *current* page.
                // We should probably ask the backend for the current page ID.
                // For now, let's just assume the first one if not set, or add an endpoint.
                // Or we can just rely on the user selecting one.
                if (!this.currentPageId && this.pages.length > 0) {
                    this.currentPageId = this.pages[0].id;
                }
            } catch (error) {
                console.error('Failed to load pages:', error);
            }
        },
        async loadButtons() {
            try {
                const response = await axios.get('/api/v1/buttons');
                this.buttons = response.data.buttons;
            } catch (error) {
                console.error('Failed to load buttons:', error);
            }
        },
        async loadPlugins() {
            try {
                const response = await axios.get('/api/v1/plugins');
                this.plugins = response.data;
            } catch (error) {
                console.error('Failed to load plugins:', error);
            }
        },
        async updateBrightness() {
            try {
                await axios.post(`/api/v1/device/brightness/${this.brightness}`);
            } catch (error) {
                console.error('Failed to update brightness:', error);
            }
        },
        async reconnectDevice() {
            try {
                await axios.post('/api/v1/device/reconnect');
                await this.loadDeviceInfo();
                await this.loadButtons();
            } catch (error) {
                console.error('Failed to reconnect device:', error);
                alert('Failed to reconnect to device');
            }
        },
        async switchPage(pageId) {
            try {
                await axios.post(`/api/v1/pages/${pageId}/activate`);
                this.currentPageId = pageId;
                await this.loadButtons();
            } catch (error) {
                console.error('Failed to switch page:', error);
            }
        },
        async createPage() {
            if (!this.newPageTitle) return;
            try {
                const response = await axios.post('/api/v1/pages', null, { params: { title: this.newPageTitle } });
                this.newPageTitle = '';
                this.showPageModal = false;
                await this.loadPages();
                await this.switchPage(response.data.id);
            } catch (error) {
                console.error('Failed to create page:', error);
            }
        },
        async deletePage(pageId) {
            if (!confirm('Are you sure you want to delete this page?')) return;
            try {
                await axios.delete(`/api/v1/pages/${pageId}`);
                await this.loadPages();
                if (this.pages.length > 0) {
                    await this.switchPage(this.pages[0].id);
                }
            } catch (error) {
                console.error('Failed to delete page:', error);
            }
        },
        editButton(button) {
            // Create a copy for editing
            this.editingButton = {
                key: button.key,
                label: button.label || '',
                enabled: button.enabled,
                font_size: button.font_size || 14,
                bg_color: button.bg_color || [0, 0, 0],
                text_color: button.text_color || [255, 255, 255],
                selectedPlugin: button.action?.plugin_id || '',
                config: button.action?.config || {}
            };
        },
        closeEditor() {
            this.editingButton = null;
        },
        onPluginChange() {
            // Reset config when plugin changes
            if (this.selectedPluginInfo) {
                this.editingButton.config = {};
            }
        },
        async saveButton() {
            try {
                const data = {
                    label: this.editingButton.label,
                    action_type: this.editingButton.selectedPlugin ? 'plugin' : 'none',
                    plugin_id: this.editingButton.selectedPlugin || null,
                    config: this.editingButton.config,
                    font_size: this.editingButton.font_size,
                    bg_color: this.editingButton.bg_color,
                    text_color: this.editingButton.text_color,
                    enabled: this.editingButton.enabled
                };

                await axios.put(`/api/v1/buttons/${this.editingButton.key}`, data);
                await this.loadButtons();
                this.closeEditor();
            } catch (error) {
                console.error('Failed to save button:', error);
                alert('Failed to save button configuration');
            }
        },
        async clearButton() {
            if (!confirm('Clear this button?')) return;

            try {
                await axios.delete(`/api/v1/buttons/${this.editingButton.key}`);
                await this.loadButtons();
                this.closeEditor();
            } catch (error) {
                console.error('Failed to clear button:', error);
                alert('Failed to clear button');
            }
        },
        async testButton() {
            try {
                await axios.post(`/api/v1/buttons/${this.editingButton.key}/press`);
            } catch (error) {
                console.error('Failed to test button:', error);
                alert('Failed to test button: ' + error.response?.data?.detail);
            }
        },
        getPluginName(pluginId) {
            const plugin = this.plugins.find(p => p.id === pluginId);
            return plugin ? plugin.name : pluginId;
        }
    },
    async mounted() {
        await this.loadDeviceInfo();
        await this.loadPlugins();
        await this.loadPages();
        await this.loadButtons();

        // Auto-refresh device status every 30 seconds
        setInterval(() => {
            this.loadDeviceInfo();
        }, 30000);
    }
}).mount('#app');
