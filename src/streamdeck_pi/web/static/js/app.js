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
      showPageModal: false,
      showMoveModal: false,
      movingButton: null,
      editingPage: null,
      showEditPageModal: false
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
        editPage() {
          const page = this.pages.find(p => p.id === this.currentPageId);
          if (!page) return;

          this.editingPage = {
            id: page.id,
            title: page.title,
            bg_color: this.rgbToHex(page.bg_color),
            text_color: this.rgbToHex(page.text_color)
          };
          this.showEditPageModal = true;
        },
    async savePage() {
          try {
            const data = {
              title: this.editingPage.title,
              bg_color: this.editingPage.bg_color ? this.hexToRgb(this.editingPage.bg_color) : null,
              text_color: this.editingPage.text_color ? this.hexToRgb(this.editingPage.text_color) : null
            };

            await axios.put(`/api/v1/pages/${this.editingPage.id}`, data);
            this.showEditPageModal = false;
            await this.loadPages();
            // Reload buttons to reflect color changes if they were using defaults
            await this.loadButtons();
          } catch (error) {
            console.error('Failed to save page:', error);
            alert('Failed to save page settings');
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
            icon: button.icon || '',
            enabled: button.enabled,
            font_size: button.font_size || 14,
            bg_color: this.rgbToHex(button.bg_color || [0, 0, 0]),
            text_color: this.rgbToHex(button.text_color || [255, 255, 255]),
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
              icon: this.editingButton.icon,
              action_type: this.editingButton.selectedPlugin ? 'plugin' : 'none',
              plugin_id: this.editingButton.selectedPlugin || null,
              config: this.editingButton.config,
              font_size: this.editingButton.font_size,
              bg_color: this.hexToRgb(this.editingButton.bg_color),
              text_color: this.hexToRgb(this.editingButton.text_color),
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
            alert('Failed to test button: ' + (error.response?.data?.detail || error.message));
          }
        },
        getPluginName(pluginId) {
          const plugin = this.plugins.find(p => p.id === pluginId);
          return plugin ? plugin.name : pluginId;
        },
        rgbToHex(rgb) {
          if (!rgb || rgb.length !== 3) return '#000000';
          return '#' + rgb.map(x => {
            const hex = x.toString(16);
            return hex.length === 1 ? '0' + hex : hex;
          }).join('');
        },
        hexToRgb(hex) {
          const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
          return result ? [
            parseInt(result[1], 16),
            parseInt(result[2], 16),
            parseInt(result[3], 16)
          ] : [0, 0, 0];
        },
        onDragStart(event, button) {
          event.dataTransfer.setData('text/plain', JSON.stringify({
            key: button.key,
            pageId: this.currentPageId
          }));
          event.dataTransfer.effectAllowed = 'move';
        },
        onDragOver(event) {
          event.preventDefault();
          event.dataTransfer.dropEffect = 'move';
        },
    async onDrop(event, targetButton) {
          event.preventDefault();
          const data = JSON.parse(event.dataTransfer.getData('text/plain'));

          if (data.pageId !== this.currentPageId) return;
          if (data.key === targetButton.key) return;

          try {
            await axios.post('/api/v1/buttons/swap', {
              page_id: this.currentPageId,
              key1: data.key,
              key2: targetButton.key
            });
            await this.loadButtons();
          } catch (error) {
            console.error('Failed to swap buttons:', error);
          }
        },
        openMoveModal(button, event) {
          event.stopPropagation();
          this.movingButton = button;
          this.showMoveModal = true;
        },
    async moveButtonToPage(targetPageId) {
          if (!this.movingButton) return;
          try {
            await axios.post('/api/v1/buttons/move', {
              source_page_id: this.currentPageId,
              source_key: this.movingButton.key,
              target_page_id: targetPageId
            });
            await this.loadButtons();
            this.showMoveModal = false;
            this.movingButton = null;
          } catch (error) {
            console.error('Failed to move button:', error);
            alert('Failed to move button: ' + (error.response?.data?.detail || error.message));
          }
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
