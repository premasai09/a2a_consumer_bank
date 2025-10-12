class ChatApp {
    constructor() {
        this.sessionId = this.generateSessionId();
        this.messageCount = 0;
        this.isProcessing = false;
        this.connectionStatus = 'connecting';
        this.bankAgents = {
            'CloudTrust Financial Agent': 'disconnected',
            'Finovate Bank Agent': 'disconnected',
            'Zentra Bank Agent': 'disconnected',
            'Byte Bank Agent': 'disconnected',
            'NexVault Bank Agent': 'disconnected'
        };
        this.settings = {
            autoScroll: true,
            sound: true,
            theme: 'light'
        };
        
        // Credit offers tracking
        this.creditOffers = [];
        this.hasCreditOffers = false;
        this.isFinalOffer = false;
        this.isRejectedOffer = false;
        
        this.init();
    }
    
    generateSessionId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    
    init() {
        this.initializeElements();
        this.setupEventListeners();
        this.updateSessionInfo();
        this.loadSettings();
        this.checkAgentConnections();
        this.setupTheme();
    }
    
    initializeElements() {
        this.elements = {
            messageInput: document.getElementById('messageInput'),
            sendBtn: document.getElementById('sendBtn'),
            chatMessages: document.getElementById('chatMessages'),
            typingIndicator: document.getElementById('typingIndicator'),
            connectionStatus: document.getElementById('connectionStatus'),
            sessionId: document.getElementById('sessionId'),
            sessionTime: document.getElementById('sessionTime'),
            messageCount: document.getElementById('messageCount'),
            statusTimeline: document.getElementById('statusTimeline'),
            charCount: document.getElementById('charCount'),
            loadingOverlay: document.getElementById('loadingOverlay'),
            progressFill: document.getElementById('progressFill'),
            progressText: document.getElementById('progressText'),
            loadingText: document.getElementById('loadingText'),
            formModal: document.getElementById('formModal'),
            modalTitle: document.getElementById('modalTitle'),
            modalBody: document.getElementById('modalBody'),
            autoScrollToggle: document.getElementById('autoScrollToggle'),
            soundToggle: document.getElementById('soundToggle'),
            themeSelect: document.getElementById('themeSelect'),
            profileIcon: document.getElementById('profileIcon'),
            creditOffersButtonContainer: document.getElementById('creditOffersButtonContainer'),
            creditOffersBtn: document.getElementById('creditOffersBtn')
        };
    }
    
    setupEventListeners() {
        // Message input events
        this.elements.messageInput.addEventListener('input', (e) => {
            this.handleInputChange(e);
            this.autoResizeTextarea(e.target);
        });
        
        this.elements.messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Send button
        this.elements.sendBtn.addEventListener('click', () => this.sendMessage());
        
        // Settings
        this.elements.autoScrollToggle.addEventListener('change', (e) => {
            this.settings.autoScroll = e.target.checked;
            this.saveSettings();
        });
        
        this.elements.soundToggle.addEventListener('change', (e) => {
            this.settings.sound = e.target.checked;
            this.saveSettings();
        });
        
        this.elements.themeSelect.addEventListener('change', (e) => {
            this.settings.theme = e.target.value;
            this.saveSettings();
            this.applyTheme();
        });
        
        // Modal events
        window.addEventListener('click', (e) => {
            if (e.target === this.elements.formModal) {
                this.closeModal();
            }
        });
        
        // Profile icon event
        if (this.elements.profileIcon) {
            this.elements.profileIcon.addEventListener('click', () => {
                this.showCompanyProfile();
            });
        }
        
        // Credit offers button event
        if (this.elements.creditOffersBtn) {
            this.elements.creditOffersBtn.addEventListener('click', () => {
                this.showCreditOffersModal();
            });
        }
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeModal();
                this.closeProfileModal();
                this.closeCreditOffersModal();
            }
        });
    }
    
    handleInputChange(e) {
        const length = e.target.value.length;
        this.elements.charCount.textContent = length;
        
        // Update send button state
        this.elements.sendBtn.disabled = length === 0 || this.isProcessing;
        
        // Color code character count
        if (length > 1800) {
            this.elements.charCount.style.color = 'var(--error-color)';
        } else if (length > 1500) {
            this.elements.charCount.style.color = 'var(--warning-color)';
        } else {
            this.elements.charCount.style.color = 'var(--text-muted)';
        }
    }
    
    autoResizeTextarea(textarea) {
        textarea.style.height = 'auto';
        const newHeight = Math.min(textarea.scrollHeight, 120);
        textarea.style.height = newHeight + 'px';
    }
    
    async sendMessage() {
        const message = this.elements.messageInput.value.trim();
        if (!message || this.isProcessing) return;
        
        // Add user message to chat
        this.addMessage('user', message);
        this.elements.messageInput.value = '';
        this.elements.charCount.textContent = '0';
        this.autoResizeTextarea(this.elements.messageInput);
        this.elements.sendBtn.disabled = true;
        
        // Show processing state
        this.setProcessingState(true);
        this.showTypingIndicator();
        
        // Update status timeline to processing
        this.updateStatusTimeline('processing', 'Processing your request...');
        
        try {
            // Send message to agent
            const response = await this.sendToAgent(message);
            this.hideTypingIndicator();
            
            // Add agent response to chat
            this.addMessage('assistant', response);
            
            // Update status based on response content
            this.updateStatusBasedOnResponse(response);
            
        } catch (error) {
            console.error('Error sending message:', error);
            this.hideTypingIndicator();
            this.addMessage('assistant', 'I apologize, but I encountered an error while processing your request. Please try again.');
            this.updateStatusTimeline('ready', 'Ready to start');
        }
        
        this.setProcessingState(false);
        this.elements.sendBtn.disabled = false;
    }
    
    updateStatusBasedOnResponse(response) {
        const lowerResponse = response.toLowerCase();
        
        if (lowerResponse.includes('contacting') || lowerResponse.includes('sending') || lowerResponse.includes('reaching out')) {
            this.updateStatusTimeline('bank_requests', 'Contacting banks...');
        } else if (lowerResponse.includes('received') && (lowerResponse.includes('offer') || lowerResponse.includes('quote'))) {
            this.updateStatusTimeline('receiving_offers', 'Receiving offers...');
        } else if (lowerResponse.includes('analyzing') || lowerResponse.includes('comparing') || lowerResponse.includes('evaluating')) {
            this.updateStatusTimeline('analyzing', 'Analyzing offers...');
        } else if (lowerResponse.includes('selected') || lowerResponse.includes('recommended') || lowerResponse.includes('best offer') || lowerResponse.includes('completed')) {
            this.updateStatusTimeline('completed', 'Process complete');
        } else if (lowerResponse.includes('credit') && (lowerResponse.includes('application') || lowerResponse.includes('request'))) {
            this.updateStatusTimeline('bank_requests', 'Contacting banks...');
        }
    }
    
    async sendToAgent(message) {
        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query: message,
                    session_id: this.sessionId
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            return data.response;

        } catch (error) {
            console.error('Error communicating with agent:', error);
            throw new Error(`Failed to communicate with agent: ${error.message}`);
        }
    }
    
    addMessage(sender, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.textContent = sender === 'user' ? 'U' : 'AI';
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        const bubble = document.createElement('div');
        bubble.className = 'message-bubble';
        
        // Format message content (support basic markdown-like formatting)
        bubble.innerHTML = this.formatMessage(content);
        
        const time = document.createElement('div');
        time.className = 'message-time';
        time.textContent = new Date().toLocaleTimeString();
        
        messageContent.appendChild(bubble);
        messageContent.appendChild(time);
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(messageContent);
        
        // Remove welcome message if it exists
        const welcomeMessage = this.elements.chatMessages.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.remove();
        }
        
        this.elements.chatMessages.appendChild(messageDiv);
        this.messageCount++;
        this.updateSessionInfo();
        
        // Check for credit offers in assistant messages
        if (sender === 'assistant') {
            // Reset offer status flags for new message
            this.isFinalOffer = false;
            this.isRejectedOffer = false;
            this.detectCreditOffers(content);
        }
        
        if (this.settings.autoScroll) {
            this.scrollToBottom();
        }
        
        if (sender === 'assistant' && this.settings.sound) {
            this.playNotificationSound();
        }
    }
    
    formatMessage(content) {
        // Basic markdown-like formatting
        return content
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>')
            .replace(/\n/g, '<br>')
            .replace(/• (.*?)(?=<br>|$)/g, '<li>$1</li>')
            .replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
    }
    
    showTypingIndicator() {
        this.elements.typingIndicator.style.display = 'flex';
        if (this.settings.autoScroll) {
            this.scrollToBottom();
        }
    }
    
    hideTypingIndicator() {
        this.elements.typingIndicator.style.display = 'none';
    }
    
    setProcessingState(processing) {
        this.isProcessing = processing;
        this.elements.messageInput.disabled = processing;
        
        if (processing) {
            this.elements.messageInput.placeholder = 'Processing your request...';
        } else {
            this.elements.messageInput.placeholder = 'Describe your credit line requirements...';
        }
    }
    
    scrollToBottom() {
        setTimeout(() => {
            this.elements.chatMessages.scrollTop = this.elements.chatMessages.scrollHeight;
        }, 100);
    }
    
    updateSessionInfo() {
        this.elements.sessionId.textContent = this.sessionId.substring(8, 20);
        this.elements.messageCount.textContent = this.messageCount.toString();
    }
    
    updateStatusTimeline(status, message) {
        // Clear existing timeline
        this.elements.statusTimeline.innerHTML = '';
        
        const statuses = [
            { id: 'ready', label: 'Ready to start', icon: 'fas fa-circle' },
            { id: 'processing', label: 'Processing request', icon: 'fas fa-cog fa-spin' },
            { id: 'bank_requests', label: 'Contacting banks', icon: 'fas fa-paper-plane' },
            { id: 'receiving_offers', label: 'Receiving offers', icon: 'fas fa-download' },
            { id: 'analyzing', label: 'Analyzing offers', icon: 'fas fa-chart-line' },
            { id: 'completed', label: 'Process complete', icon: 'fas fa-check' }
        ];
        
        statuses.forEach((s, index) => {
            const item = document.createElement('div');
            item.className = 'timeline-item';
            
            if (s.id === status) {
                item.classList.add('active');
            } else if (statuses.findIndex(st => st.id === status) > index) {
                item.classList.add('completed');
            }
            
            item.innerHTML = `
                <div class="timeline-icon">
                    <i class="${s.icon}"></i>
                </div>
                <div class="timeline-content">
                    <span>${s.id === status ? message : s.label}</span>
                </div>
            `;
            
            this.elements.statusTimeline.appendChild(item);
        });
    }
    
    async checkAgentConnections() {
        try {
            const response = await fetch('/api/agent-status');
            if (response.ok) {
                const data = await response.json();
                
                if (data.consumer_agent_ready) {
                    this.updateConnectionStatus('connected');
                    
                    // Update bank agent statuses
                    for (const [bankName, status] of Object.entries(data.bank_agents)) {
                        this.updateBankAgentStatus(bankName, status.connected ? 'connected' : 'disconnected');
                    }
                } else {
                    this.updateConnectionStatus('disconnected');
                }
            } else {
                this.updateConnectionStatus('disconnected');
            }
        } catch (error) {
            console.error('Error checking agent connections:', error);
            this.updateConnectionStatus('disconnected');
        }
    }
    
    updateConnectionStatus(status) {
        this.connectionStatus = status;
        const statusElement = this.elements.connectionStatus;
        const icon = statusElement.querySelector('i');
        const text = statusElement.querySelector('span');
        
        statusElement.className = `status-indicator ${status}`;
        
        switch (status) {
            case 'connected':
                icon.className = 'fas fa-circle';
                text.textContent = 'Connected Bank Agents';
                break;
            case 'connecting':
                icon.className = 'fas fa-circle-notch';
                text.textContent = 'Connecting...';
                break;
            case 'disconnected':
                icon.className = 'fas fa-circle';
                text.textContent = 'Disconnected';
                break;
        }
    }
    
    updateBankAgentStatus(agentName, status) {
        this.bankAgents[agentName] = status;
        
        // Update agent badge
        let badgeId;
        if (agentName.includes('CloudTrust')) badgeId = 'agent-cloudtrust';
        else if (agentName.includes('Finovate')) badgeId = 'agent-finovate';
        else if (agentName.includes('Zentra')) badgeId = 'agent-zentra';
        else if (agentName.includes('Byte')) badgeId = 'agent-byte';
        else if (agentName.includes('NexVault')) badgeId = 'agent-nexvault';

        
        if (badgeId) {
            const badge = document.getElementById(badgeId);
            if (badge) {
                badge.className = `agent-badge ${status}`;
            }
        }
    }
    
    showLoadingOverlay(title, message) {
        this.elements.loadingText.textContent = message;
        this.elements.loadingOverlay.style.display = 'flex';
        
        // Simulate progress
        let progress = 0;
        const interval = setInterval(() => {
            progress += Math.random() * 15;
            if (progress >= 100) {
                progress = 100;
                clearInterval(interval);
            }
            
            this.elements.progressFill.style.width = `${progress}%`;
            this.elements.progressText.textContent = `${Math.round(progress)}%`;
        }, 200);
    }
    
    hideLoadingOverlay() {
        this.elements.loadingOverlay.style.display = 'none';
        this.elements.progressFill.style.width = '0%';
        this.elements.progressText.textContent = '0%';
    }
    
    showModal(title, content) {
        this.elements.modalTitle.textContent = title;
        this.elements.modalBody.innerHTML = content;
        this.elements.formModal.style.display = 'flex';
    }
    
    closeModal() {
        this.elements.formModal.style.display = 'none';
    }
    
    setupTheme() {
        // Initialize theme
        const savedTheme = localStorage.getItem('chat-theme') || 'light';
        this.settings.theme = savedTheme;
        this.elements.themeSelect.value = savedTheme;
        this.applyTheme();
    }
    
    applyTheme() {
        const theme = this.settings.theme;
        
        if (theme === 'auto') {
            // Use system preference
            const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            document.documentElement.setAttribute('data-theme', prefersDark ? 'dark' : 'light');
        } else {
            document.documentElement.setAttribute('data-theme', theme);
        }
    }
    
    loadSettings() {
        const settings = localStorage.getItem('chat-settings');
        if (settings) {
            this.settings = { ...this.settings, ...JSON.parse(settings) };
            this.elements.autoScrollToggle.checked = this.settings.autoScroll;
            this.elements.soundToggle.checked = this.settings.sound;
            this.elements.themeSelect.value = this.settings.theme;
        }
        
        // Update session start time
        this.elements.sessionTime.textContent = new Date().toLocaleTimeString();
    }
    
    saveSettings() {
        localStorage.setItem('chat-settings', JSON.stringify(this.settings));
    }
    
    playNotificationSound() {
        if (this.settings.sound) {
            // Create a simple notification sound
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            oscillator.frequency.value = 800;
            oscillator.type = 'sine';
            gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.1);
            
            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.1);
        }
    }
    
    async showCompanyProfile() {
        try {
            // First try to fetch real company data from the backend
            const companyData = await this.fetchCompanyConfig();
            this.displayCompanyProfile(companyData);
        } catch (error) {
            console.error('Error fetching company profile:', error);
            // Fall back to default/mock data
            const mockData = this.getMockCompanyData();
            this.displayCompanyProfile(mockData);
        }
    }
    
    async fetchCompanyConfig() {
        const response = await fetch('/api/company-config');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    }
    
    getMockCompanyData() {
        // This method should no longer be used as we fetch real data from company_config
        // Keeping it as fallback only in case of network errors
        throw new Error('Should fetch real company data from /api/company-config endpoint');
    }
    
    displayCompanyProfile(data) {
        const profileContent = this.generateProfileHTML(data);
        
        // Create profile modal
        const modal = document.createElement('div');
        modal.className = 'profile-modal';
        modal.id = 'profileModal';
        
        modal.innerHTML = `
            <div class="profile-modal-content">
                <div class="profile-modal-header">
                    <h3>
                        <i class="fas fa-building"></i>
                        Company Profile
                    </h3>
                    <button class="modal-close" onclick="closeProfileModal()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="profile-modal-body">
                    ${profileContent}
                </div>
            </div>
        `;
        
        // Add to document
        document.body.appendChild(modal);
        
        // Show modal
        modal.style.display = 'flex';
        
        // Add click outside to close
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                this.closeProfileModal();
            }
        });
    }
    
    generateProfileHTML(data) {
        const formatCurrency = (amount) => {
            return new Intl.NumberFormat('en-US', {
                style: 'currency',
                currency: 'USD'
            }).format(amount);
        };
        
        const formatNumber = (num) => {
            return new Intl.NumberFormat('en-US').format(num);
        };
        
        const formatDate = (dateString) => {
            return new Date(dateString).toLocaleString();
        };
        
        const esgCertifications = data.esg_certifications ? data.esg_certifications.split(',') : [];
        const disclosures = data.regulatory_context_required_disclosures ? data.regulatory_context_required_disclosures.split(',') : [];
        
        return `
            <div class="profile-section-group">
                <h4 class="profile-section-title">
                    <i class="fas fa-building"></i>
                    Company Information
                </h4>
                <div class="profile-info-grid">
                    <div class="profile-info-item">
                        <div class="profile-info-label">Company Name</div>
                        <div class="profile-info-value">${data.sender_name || 'Not specified'}</div>
                    </div>
                    <div class="profile-info-item">
                        <div class="profile-info-label">DUNS Number</div>
                        <div class="profile-info-value code">${data.sender_id || 'Not specified'}</div>
                    </div>
                    <div class="profile-info-item">
                        <div class="profile-info-label">Registration Number</div>
                        <div class="profile-info-value code">${data.company_registration_number || 'Not specified'}</div>
                    </div>
                    <div class="profile-info-item">
                        <div class="profile-info-label">Jurisdiction</div>
                        <div class="profile-info-value">${data.jurisdiction || 'Not specified'}</div>
                    </div>
                    <div class="profile-info-item">
                        <div class="profile-info-label">Industry Code (NAICS)</div>
                        <div class="profile-info-value code">${data.industry_code || 'Not specified'}</div>
                    </div>
                    <div class="profile-info-item">
                        <div class="profile-info-label">Tax ID (EIN)</div>
                        <div class="profile-info-value code">${data.tax_id || 'Not specified'}</div>
                    </div>
                </div>
            </div>
            
            <div class="profile-section-group">
                <h4 class="profile-section-title">
                    <i class="fas fa-chart-line"></i>
                    Financial Information
                </h4>
                <div class="profile-info-grid">
                    <div class="profile-info-item">
                        <div class="profile-info-label">Annual Revenue</div>
                        <div class="profile-info-value currency">${data.financials_annual_revenue ? formatCurrency(data.financials_annual_revenue) : 'Not specified'}</div>
                    </div>
                    <div class="profile-info-item">
                        <div class="profile-info-label">Net Income</div>
                        <div class="profile-info-value currency">${data.financials_net_income ? formatCurrency(data.financials_net_income) : 'Not specified'}</div>
                    </div>
                    <div class="profile-info-item">
                        <div class="profile-info-label">Total Assets</div>
                        <div class="profile-info-value currency">${data.financials_assets_total ? formatCurrency(data.financials_assets_total) : 'Not specified'}</div>
                    </div>
                    <div class="profile-info-item">
                        <div class="profile-info-label">Total Liabilities</div>
                        <div class="profile-info-value currency">${data.financials_liabilities_total ? formatCurrency(data.financials_liabilities_total) : 'Not specified'}</div>
                    </div>
                    <div class="profile-info-item">
                        <div class="profile-info-label">Credit Report Reference</div>
                        <div class="profile-info-value code">${data.credit_report_ref || 'Not specified'}</div>
                    </div>
                    <div class="profile-info-item">
                        <div class="profile-info-label">ESG Impact Ratio</div>
                        <div class="profile-info-value percentage">${data.ESG_impact_ratio ? (parseFloat(data.ESG_impact_ratio) * 100).toFixed(1) + '%' : 'Not specified'}</div>
                    </div>
                </div>
            </div>
            
            <div class="profile-section-group">
                <h4 class="profile-section-title">
                    <i class="fas fa-leaf"></i>
                    ESG Information
                </h4>
                <div class="profile-info-grid">
                    <div class="profile-info-item">
                        <div class="profile-info-label">Carbon Emissions (tons CO2e)</div>
                        <div class="profile-info-value">${data.carbon_emissions_tons_co2e ? formatNumber(data.carbon_emissions_tons_co2e) : 'Not specified'}</div>
                    </div>
                    <div class="profile-info-item">
                        <div class="profile-info-label">ESG Certifications</div>
                        <div class="profile-info-value">
                            ${esgCertifications.length > 0 ? 
                                '<div class="profile-badges">' + 
                                esgCertifications.map(cert => `<span class="profile-badge">${cert.trim()}</span>`).join('') + 
                                '</div>' : 'None specified'}
                        </div>
                    </div>
                    <div class="profile-info-item">
                        <div class="profile-info-label">ESG Reporting URL</div>
                        <div class="profile-info-value">
                            ${data.esg_reporting_url ? 
                                `<a href="${data.esg_reporting_url}" target="_blank" style="color: var(--primary-color); text-decoration: none;">${data.esg_reporting_url}</a>` : 
                                'Not specified'}
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="profile-section-group">
                <h4 class="profile-section-title">
                    <i class="fas fa-gavel"></i>
                    Regulatory Information
                </h4>
                <div class="profile-info-grid">
                    <div class="profile-info-item">
                        <div class="profile-info-label">Regulatory Jurisdiction</div>
                        <div class="profile-info-value">${data.regulatory_context_jurisdiction || 'Not specified'}</div>
                    </div>
                    <div class="profile-info-item">
                        <div class="profile-info-label">Required Disclosures</div>
                        <div class="profile-info-value">
                            ${disclosures.length > 0 ? 
                                '<div class="profile-badges">' + 
                                disclosures.map(disc => `<span class="profile-badge">${disc.trim()}</span>`).join('') + 
                                '</div>' : 'None specified'}
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="profile-section-group">
                <h4 class="profile-section-title">
                    <i class="fas fa-cogs"></i>
                    Technical Information
                </h4>
                <div class="profile-info-grid">
                    <div class="profile-info-item">
                        <div class="profile-info-label">Protocol Version</div>
                        <div class="profile-info-value code">${data.protocol_version || 'Not specified'}</div>
                    </div>
                </div>
            </div>
            
            <div style="margin-top: var(--space-2xl); padding: var(--space-lg); background: var(--bg-secondary); border-radius: var(--radius-md); border-left: 4px solid var(--primary-color);">
                <h5 style="color: var(--primary-color); margin-bottom: var(--space-sm);">
                    <i class="fas fa-info-circle"></i>
                    About This Information
                </h5>
                <p style="color: var(--text-secondary); font-size: var(--font-size-sm); line-height: 1.5;">
                    This profile shows the company information that will be automatically included with your credit applications. 
                    This data helps banks assess your creditworthiness and ensures compliance with regulatory requirements. 
                    All information is transmitted securely and in accordance with data protection standards.
                </p>
            </div>
        `;
    }
    
    closeProfileModal() {
        const modal = document.getElementById('profileModal');
        if (modal) {
            modal.remove();
        }
    }
    
    detectCreditOffers(content) {
        // Look for patterns that indicate credit offers or loan information
        const offerPatterns = [
            /credit.*offer/i,
            /loan.*offer/i,
            /interest.*rate/i,
            /bank.*response/i,
            /offer.*from.*bank/i,
            /credit.*line/i,
            /loan.*amount/i,
            /annual.*rate/i,
            /repayment.*term/i,
            /bank.*agent.*response/i,
            /display_offers/i,
            /received_offers/i,
            /amount.*approved/i,
            /\$\d+/i,  // Any dollar amount
            /\d+\.\d*%/i,  // Any percentage
            /byte.*bank/i,
            /cloudtrust/i,
            /finovate/i,
            /zentra/i,
            /nexvault/i
        ];
        
        const hasOfferPattern = offerPatterns.some(pattern => pattern.test(content));
        
        if (hasOfferPattern) {
            // Enhanced debugging for offer extraction
            console.log('=== ENHANCED OFFER EXTRACTION DEBUG ===');
            console.log('Full message content:', content);
            console.log('Content length:', content.length);
            
            // Clear previous offers when new message arrives
            this.creditOffers = [];
            
            const extractedOffers = this.extractOfferData(content);
            console.log('Extracted offers from content:', extractedOffers);
            console.log('Number of offers found:', extractedOffers.length);
            
            // Enhanced debugging for each offer
            extractedOffers.forEach((offer, index) => {
                console.log(`--- OFFER ${index + 1} DETAILED DEBUG ---`);
                console.log('Raw offer data:', offer);
                console.log('Bank ID/Name:', offer.bankid || offer.bankname || offer.bank_name);
                console.log('Amount (approved):', offer.amount_approved);
                console.log('Amount (value):', offer.amount_value);
                console.log('Interest Rate:', offer.interest_rate_annual || offer.interest_rate);
                console.log('Duration:', offer.repayment_duration_months || offer.repayment_duration);
                console.log('Status:', offer.status);
                console.log('ESG Summary:', offer.esg_impact_summary);
                console.log('--- END OFFER ${index + 1} DEBUG ---');
            });
            
            if (extractedOffers.length > 0) {
                this.creditOffers = extractedOffers;
                this.hasCreditOffers = true;
                this.showCreditOffersButton();
                console.log('Credit offers button shown for', extractedOffers.length, 'offers');
            } else {
                console.log('No valid offers found - searching with text parsing fallback');
                // Try enhanced text parsing as final fallback
                const textParsedOffers = this.enhancedTextParsing(content);
                if (textParsedOffers.length > 0) {
                    this.creditOffers = textParsedOffers;
                    this.hasCreditOffers = true;
                    this.showCreditOffersButton();
                    console.log('Fallback text parsing found', textParsedOffers.length, 'offers');
                }
            }
            console.log('=== END ENHANCED OFFER EXTRACTION DEBUG ===');
        }
        
        // ...existing code...
    }
    
    enhancedTextParsing(content) {
        const offers = [];
        console.log('=== ENHANCED TEXT PARSING FALLBACK ===');
        
        // More comprehensive bank name variations and agent patterns
        const bankPatterns = [
            { name: 'Byte Bank', patterns: [/byte.*bank/i, /bank.*agent.*5/i, /agent.*byte/i] },
            { name: 'CloudTrust Financial', patterns: [/cloudtrust/i, /cloud.*trust/i, /bank.*agent.*1/i, /agent.*cloudtrust/i] },
            { name: 'Finovate Bank', patterns: [/finovate/i, /finos?ate/i, /bank.*agent.*2/i, /agent.*finovate/i] },
            { name: 'Zentra Bank', patterns: [/zentra/i, /zentral/i, /bank.*agent.*3/i, /agent.*zentra/i] },
            { name: 'NexVault Bank', patterns: [/nexvault/i, /nex.*vault/i, /bank.*agent.*4/i, /agent.*nexvault/i] }
        ];
        
        // Enhanced patterns for extracting offer information
        const enhancedAmountPatterns = [
            /amount.*approved[:\s]*\$?([\d,]+(?:\.\d+)?)/i,
            /approved.*amount[:\s]*\$?([\d,]+(?:\.\d+)?)/i,
            /credit.*amount[:\s]*\$?([\d,]+(?:\.\d+)?)/i,
            /loan.*amount[:\s]*\$?([\d,]+(?:\.\d+)?)/i,
            /\$\s*([\d,]+(?:\.\d+)?)\s*(?:million|thousand|m|k)?/i,
            /(?:offered|providing|approved).*\$\s*([\d,]+(?:\.\d+)?)/i
        ];
        
        const enhancedRatePatterns = [
            /interest.*rate[:\s]*(\d+\.?\d*)\s*%/i,
            /annual.*rate[:\s]*(\d+\.?\d*)\s*%/i,
            /rate[:\s]*(\d+\.?\d*)\s*%.*annual/i,
            /(\d+\.?\d*)\s*%.*(?:interest|annual|rate)/i
        ];
        
        const enhancedTermPatterns = [
            /repayment.*duration[:\s]*(\d+)\s*months?/i,
            /duration[:\s]*(\d+)\s*months?/i,
            /term[:\s]*(\d+)\s*months?/i,
            /(\d+)\s*months?.*(?:repayment|term|duration)/i
        ];
        
        // ESG summary patterns
        const esgPatterns = [
            /esg.*impact.*summary[:\s]*([^.]+(?:\.[^.]*){0,3})/i,
            /esg.*summary[:\s]*([^.]+(?:\.[^.]*){0,3})/i,
            /environmental.*social.*governance[:\s]*([^.]+(?:\.[^.]*){0,3})/i
        ];
        
        // Search for each bank and extract associated data
        bankPatterns.forEach(bank => {
            let bankFound = false;
            let bankSection = '';
            
            // Check if any bank pattern matches
            bank.patterns.forEach(pattern => {
                const match = content.match(pattern);
                if (match && !bankFound) {
                    bankFound = true;
                    console.log(`Found ${bank.name} using pattern:`, pattern);
                    
                    // Extract a larger section around the bank mention
                    const matchIndex = content.toLowerCase().indexOf(match[0].toLowerCase());
                    const start = Math.max(0, matchIndex - 500);
                    const end = Math.min(content.length, matchIndex + match[0].length + 1000);
                    bankSection = content.substring(start, end);
                    
                    console.log(`Bank section for ${bank.name}:`, bankSection.substring(0, 200) + '...');
                }
            });
            
            if (bankFound) {
                const offer = { bankid: bank.name, currency: 'USD' };
                
                // Extract amount
                let amountFound = false;
                enhancedAmountPatterns.forEach(pattern => {
                    if (!amountFound) {
                        const match = bankSection.match(pattern);
                        if (match) {
                            let amount = parseFloat(match[1].replace(/,/g, ''));
                            
                            // Handle million/thousand multipliers
                            if (bankSection.toLowerCase().includes('million') || 
                                bankSection.toLowerCase().includes(' m ') ||
                                match[0].toLowerCase().includes('m')) {
                                amount *= 1000000;
                            } else if (bankSection.toLowerCase().includes('thousand') || 
                                      bankSection.toLowerCase().includes(' k ') ||
                                      match[0].toLowerCase().includes('k')) {
                                amount *= 1000;
                            }
                            
                            if (amount > 0) {
                                offer.amount_approved = amount;
                                offer.amount_value = amount;
                                amountFound = true;
                                console.log(`Found amount for ${bank.name}: $${amount}`);
                            }
                        }
                    }
                });
                
                // Extract interest rate
                let rateFound = false;
                enhancedRatePatterns.forEach(pattern => {
                    if (!rateFound) {
                        const match = bankSection.match(pattern);
                        if (match) {
                            const rate = parseFloat(match[1]);
                            if (rate > 0 && rate < 50) { // Reasonable rate range
                                offer.interest_rate_annual = rate;
                                rateFound = true;
                                console.log(`Found rate for ${bank.name}: ${rate}%`);
                            }
                        }
                    }
                });
                
                // Extract term/duration
                let termFound = false;
                enhancedTermPatterns.forEach(pattern => {
                    if (!termFound) {
                        const match = bankSection.match(pattern);
                        if (match) {
                            const term = parseInt(match[1]);
                            if (term > 0 && term <= 120) { // Reasonable term range
                                offer.repayment_duration_months = term;
                                offer.repayment_duration = term;
                                termFound = true;
                                console.log(`Found term for ${bank.name}: ${term} months`);
                            }
                        }
                    }
                });
                
                // Extract ESG summary
                esgPatterns.forEach(pattern => {
                    if (!offer.esg_impact_summary) {
                        const match = bankSection.match(pattern);
                        if (match) {
                            offer.esg_impact_summary = match[1].trim();
                            console.log(`Found ESG summary for ${bank.name}: ${match[1].substring(0, 100)}...`);
                        }
                    }
                });
                
                // Generate offer ID
                offer.offer_id = `offer_${bank.name.toLowerCase().replace(/\s+/g, '_')}_${Date.now()}`;
                
                // Set status
                offer.status = this.determineOfferStatus(offer, content);
                
                // Only add if we found at least an amount
                if (offer.amount_approved && offer.amount_approved > 0) {
                    offers.push(offer);
                    console.log(`Successfully extracted offer for ${bank.name}:`, offer);
                } else {
                    console.log(`Skipping ${bank.name} - no valid amount found`);
                }
            }
        });
        
        console.log('=== END ENHANCED TEXT PARSING ===');
        console.log('Total offers extracted:', offers.length);
        return offers;
    }
    
    extractOfferData(content) {
        const offers = [];
        
        // First, try to parse responses from the backend's send_credit_request format
        const responseArrayPattern = /\[[\s\S]*?\]/;
        const responseArrayMatch = content.match(responseArrayPattern);
        if (responseArrayMatch) {
            try {
                const responseArray = JSON.parse(responseArrayMatch[0]);
                console.log('Found response array:', responseArray);
                
                responseArray.forEach(responseItem => {
                    if (responseItem.response && !responseItem.error) {
                        try {
                            let offerData = responseItem.response;
                            
                            // If response is a string, try to parse it
                            if (typeof offerData === 'string') {
                                offerData = JSON.parse(offerData);
                            }
                            
                            // Extract bank name from response item or offer data
                            const bankName = responseItem.bank || offerData.bank?.bank_name || offerData.bankid;
                            
                            // Map the backend offer structure to our expected format
                            const mappedOffer = this.mapBackendOfferToFrontend(offerData, bankName);
                            if (mappedOffer && this.isValidOffer(mappedOffer)) {
                                mappedOffer.status = this.determineOfferStatus(mappedOffer, content);
                                offers.push(mappedOffer);
                            }
                        } catch (e) {
                            console.log('Failed to parse response item:', e, responseItem);
                        }
                    }
                });
            } catch (e) {
                console.log('Failed to parse response array:', e);
            }
        }
        
        // If no offers found from response array, try other extraction methods
        if (offers.length === 0) {
            // Try to find complete JSON objects in the content
            const completeJsonMatches = this.findCompleteJsonObjects(content);
            console.log('Found complete JSON matches:', completeJsonMatches);
            if (completeJsonMatches.length > 0) {
                completeJsonMatches.forEach(jsonStr => {
                    try {
                        const offer = JSON.parse(jsonStr);
                        console.log('Parsed offer from complete JSON:', offer);
                        if (this.isValidOffer(offer)) {
                            offer.status = this.determineOfferStatus(offer, content);
                            offers.push(offer);
                        }
                    } catch (e) {
                        console.log('Failed to parse complete JSON:', e);
                    }
                });
            }
        }
        
        // If no complete JSON found, try to find partial JSON structures
        if (offers.length === 0) {
            const partialMatches = content.match(/\{[^{}]*"bankid"[^{}]*\}/g);
            if (partialMatches) {
                partialMatches.forEach(match => {
                    try {
                        const offer = JSON.parse(match);
                        if (this.isValidOffer(offer)) {
                            offer.status = this.determineOfferStatus(offer, content);
                            offers.push(offer);
                        }
                    } catch (e) {
                        // Try to extract data manually if JSON parsing fails
                        const manualOffer = this.extractManualOfferData(match);
                        if (manualOffer) {
                            manualOffer.status = this.determineOfferStatus(manualOffer, content);
                            offers.push(manualOffer);
                        }
                    }
                });
            }
        }
        
        // Try to find nested JSON structures (from host_tools.py response format)
        if (offers.length === 0) {
            const nestedMatches = this.findNestedJsonStructures(content);
            console.log('Found nested JSON matches:', nestedMatches);
            nestedMatches.forEach(jsonStr => {
                try {
                    const data = JSON.parse(jsonStr);
                    // Handle different response formats
                    if (data.response) {
                        try {
                            const offer = JSON.parse(data.response);
                            if (this.isValidOffer(offer)) {
                                offer.status = this.determineOfferStatus(offer, content);
                                offers.push(offer);
                            }
                        } catch (e) {
                            // If response is not JSON, treat it as the offer data itself
                            if (this.isValidOffer(data.response)) {
                                data.response.status = this.determineOfferStatus(data.response, content);
                                offers.push(data.response);
                            }
                        }
                    } else if (this.isValidOffer(data)) {
                        data.status = this.determineOfferStatus(data, content);
                        offers.push(data);
                    }
                } catch (e) {
                    console.log('Failed to parse nested JSON:', e);
                }
            });
        }
        
        // If still no offers found, try to extract from text patterns
        if (offers.length === 0) {
            const textOffers = this.extractOffersFromText(content);
            offers.push(...textOffers);
        }
        
        return offers;
    }
    
    findNestedJsonStructures(content) {
        const jsonObjects = [];
        let braceCount = 0;
        let startIndex = -1;
        
        for (let i = 0; i < content.length; i++) {
            if (content[i] === '{') {
                if (braceCount === 0) {
                    startIndex = i;
                }
                braceCount++;
            } else if (content[i] === '}') {
                braceCount--;
                if (braceCount === 0 && startIndex !== -1) {
                    const jsonStr = content.substring(startIndex, i + 1);
                    // Check if this looks like a response structure
                    if (jsonStr.includes('"response"') || jsonStr.includes('"bank"') || 
                        jsonStr.includes('"signature_verified"') || jsonStr.includes('"error"')) {
                        jsonObjects.push(jsonStr);
                    }
                }
            }
        }
        
        return jsonObjects;
    }
    
    findCompleteJsonObjects(content) {
        const jsonObjects = [];
        let braceCount = 0;
        let startIndex = -1;
        
        for (let i = 0; i < content.length; i++) {
            if (content[i] === '{') {
                if (braceCount === 0) {
                    startIndex = i;
                }
                braceCount++;
            } else if (content[i] === '}') {
                braceCount--;
                if (braceCount === 0 && startIndex !== -1) {
                    const jsonStr = content.substring(startIndex, i + 1);
                    // Check if this looks like an offer JSON
                    if (jsonStr.includes('"bankid"') || jsonStr.includes('"bankname"') || 
                        jsonStr.includes('"amount_approved"') || jsonStr.includes('"amount_value"')) {
                        jsonObjects.push(jsonStr);
                    }
                }
            }
        }
        
        return jsonObjects;
    }
    
    isValidOffer(offer) {
        // Check if the offer has the minimum required fields
        // Only require bank name and amount - other fields are optional
        return (offer.bankid || offer.bankname) && 
               (offer.amount_approved || offer.amount_value);
    }
    
    extractOffersFromText(content) {
        const offers = [];
        
        // Look for bank names and associated data in the text
        const bankNames = ['CloudTrust Financial', 'Finovate Bank', 'Zentra Bank', 'Byte Bank', 'NexVault Bank'];
        
        bankNames.forEach(bankName => {
            const bankRegex = new RegExp(bankName, 'gi');
            const bankMatch = content.match(bankRegex);
            
            if (bankMatch) {
                // Try to extract offer data near this bank name
                const offerData = this.extractOfferDataNearBank(content, bankName);
                if (offerData) {
                    offerData.status = this.determineOfferStatus(offerData, content);
                    offers.push(offerData);
                }
            }
        });
        
        return offers;
    }
    
    extractOfferDataNearBank(content, bankName) {
        // Find the position of the bank name
        const bankIndex = content.toLowerCase().indexOf(bankName.toLowerCase());
        if (bankIndex === -1) return null;
        
        // Extract a section around the bank name (1000 characters before and after for better context)
        const start = Math.max(0, bankIndex - 1000);
        const end = Math.min(content.length, bankIndex + bankName.length + 1000);
        const section = content.substring(start, end);
        
        // Try to extract key data from this section with more specific patterns
        const amountPatterns = [
            /\$([\d,]+(?:\.\d{2})?)\s*(?:million|thousand|k|m)?/i,
            /amount[:\s]*\$?([\d,]+(?:\.\d{2})?)/i,
            /credit[:\s]*\$?([\d,]+(?:\.\d{2})?)/i,
            /loan[:\s]*\$?([\d,]+(?:\.\d{2})?)/i,
            /approved[:\s]*\$?([\d,]+(?:\.\d{2})?)/i,
            /value[:\s]*\$?([\d,]+(?:\.\d{2})?)/i,
            /final[:\s]*\$?([\d,]+(?:\.\d{2})?)/i,
            /total[:\s]*\$?([\d,]+(?:\.\d{2})?)/i
        ];
        
        const ratePatterns = [
            /(\d+\.?\d*)\s*%\s*(?:annual|interest|rate)/i,
            /interest[:\s]*(\d+\.?\d*)\s*%/i,
            /rate[:\s]*(\d+\.?\d*)\s*%/i,
            /annual[:\s]*(\d+\.?\d*)\s*%/i,
            /final[:\s]*(\d+\.?\d*)\s*%/i,
            /approved[:\s]*(\d+\.?\d*)\s*%/i,
            /credit[:\s]*(\d+\.?\d*)\s*%/i
        ];
        
        const termPatterns = [
            /(\d+)\s*(?:month|year)s?\s*(?:term|duration|period)/i,
            /term[:\s]*(\d+)\s*(?:month|year)/i,
            /duration[:\s]*(\d+)\s*(?:month|year)/i,
            /repayment[:\s]*(\d+)\s*(?:month|year)/i
        ];
        
        let amount = null;
        let rate = null;
        let term = null;
        
        // Try to find amount
        for (const pattern of amountPatterns) {
            const match = section.match(pattern);
            if (match) {
                amount = parseFloat(match[1].replace(/,/g, ''));
                
                // Handle million/thousand indicators
                if (section.toLowerCase().includes('million') || section.toLowerCase().includes('m')) {
                    amount *= 1000000;
                } else if (section.toLowerCase().includes('thousand') || section.toLowerCase().includes('k')) {
                    amount *= 1000;
                }
                break;
            }
        }
        
        // Try to find interest rate
        for (const pattern of ratePatterns) {
            const match = section.match(pattern);
            if (match) {
                rate = parseFloat(match[1]);
                break;
            }
        }
        
        // Try to find term
        for (const pattern of termPatterns) {
            const match = section.match(pattern);
            if (match) {
                term = parseInt(match[1]);
                break;
            }
        }
        
        // Only return an offer if we found at least the amount
        if (amount && amount > 0) {
            const offer = {
                bankid: bankName,
                amount_approved: amount,
                amount_value: amount,
                currency: 'USD'
            };
            
            if (rate && rate > 0) {
                offer.interest_rate_annual = rate;
            }
            
            if (term && term > 0) {
                offer.repayment_duration_months = term;
            }
            
            return offer;
        }
        
        return null;
    }
    
    determineOfferStatus(offer, content) {
        // Check if offer has explicit status first
        if (offer.status) {
            const status = offer.status.toLowerCase();
            // Normalize status values
            if (status === 'approved' || status === 'approve' || status === 'accept') {
                return 'approved';
            } else if (status === 'accepted' || status === 'accept') {
                return 'accepted';
            } else if (status === 'rejected' || status === 'reject' || status === 'declined' || status === 'denied') {
                return 'rejected';
            } else if (status === 'pending' || status === 'processing') {
                return 'pending';
            }
            return status;
        }
        
        // Check for final agreed upon offers
        if (this.isFinalOffer || content.toLowerCase().includes('final agreed upon offer') || 
            content.toLowerCase().includes('thank you for accepting') ||
            content.toLowerCase().includes('offer has been accepted') ||
            content.toLowerCase().includes('agreed upon offer')) {
            return 'accepted';
        }
        
        // Check for rejected offers
        if (this.isRejectedOffer || content.toLowerCase().includes('rejected') || 
            content.toLowerCase().includes('declined') || 
            content.toLowerCase().includes('not approved') ||
            content.toLowerCase().includes('application denied') ||
            content.toLowerCase().includes('unable to approve') ||
            content.toLowerCase().includes('sorry, we cannot')) {
            return 'rejected';
        }
        
        // Check for pending status
        if (content.toLowerCase().includes('pending') || 
            content.toLowerCase().includes('processing') ||
            content.toLowerCase().includes('under review')) {
            return 'pending';
        }
        
        // Default to approved for new offers
        return 'approved';
    }
    
    extractManualOfferData(text) {
        // Extract bank information (try multiple field names)
        const bankMatch = text.match(/"bankid":\s*"([^"]+)"/) || 
                         text.match(/"bankname":\s*"([^"]+)"/) ||
                         text.match(/"bank":\s*"([^"]+)"/);
        
        // Extract amount information (try multiple field names and formats)
        const amountMatch = text.match(/"amount_approved":\s*(\d+(?:\.\d+)?)/) || 
                           text.match(/"amount_value":\s*(\d+(?:\.\d+)?)/) ||
                           text.match(/"amount":\s*(\d+(?:\.\d+)?)/) ||
                           text.match(/"credit_amount":\s*(\d+(?:\.\d+)?)/) ||
                           text.match(/"loan_amount":\s*(\d+(?:\.\d+)?)/) ||
                           text.match(/"approved_amount":\s*(\d+(?:\.\d+)?)/) ||
                           text.match(/"final_amount":\s*(\d+(?:\.\d+)?)/);
        
        // Extract interest rate (try multiple field names and formats)
        const rateMatch = text.match(/"interest_rate_annual":\s*([\d.]+)/) ||
                         text.match(/"interest_rate":\s*([\d.]+)/) ||
                         text.match(/"rate":\s*([\d.]+)/) ||
                         text.match(/"annual_rate":\s*([\d.]+)/) ||
                         text.match(/"final_rate":\s*([\d.]+)/) ||
                         text.match(/"approved_rate":\s*([\d.]+)/) ||
                         text.match(/"credit_rate":\s*([\d.]+)/);
        
        // Extract repayment duration (try multiple field names)
        const durationMatch = text.match(/"repayment_duration_months":\s*(\d+)/) ||
                             text.match(/"repayment_duration":\s*(\d+)/) ||
                             text.match(/"duration":\s*(\d+)/) ||
                             text.match(/"term":\s*(\d+)/) ||
                             text.match(/"months":\s*(\d+)/);
        
        // Extract offer ID
        const offerIdMatch = text.match(/"offer_id":\s*"([^"]+)"/) ||
                            text.match(/"id":\s*"([^"]+)"/);
        
        // Extract status
        const statusMatch = text.match(/"status":\s*"([^"]+)"/) ||
                           text.match(/"approval_status":\s*"([^"]+)"/) ||
                           text.match(/"offer_status":\s*"([^"]+)"/) ||
                           text.match(/"decision":\s*"([^"]+)"/) ||
                           text.match(/"result":\s*"([^"]+)"/);
        
        // Extract currency
        const currencyMatch = text.match(/"currency":\s*"([^"]+)"/);
        
        // Extract created date
        const dateMatch = text.match(/"created_date":\s*"([^"]+)"/) ||
                         text.match(/"date":\s*"([^"]+)"/);
        
        // Extract ESG impact summary
        const esgMatch = text.match(/"esg_impact_summary":\s*"([^"]+)"/) ||
                        text.match(/"esg_summary":\s*"([^"]+)"/);
        
        // Extract status message
        const statusMsgMatch = text.match(/"status_message":\s*"([^"]+)"/) ||
                              text.match(/"message":\s*"([^"]+)"/);
        
        // Extract repayment schedule
        const scheduleMatch = text.match(/"repayment_schedule":\s*"([^"]+)"/) ||
                             text.match(/"schedule":\s*"([^"]+)"/);
        
        if (bankMatch && amountMatch) {
            const offer = {
                bankid: bankMatch[1],
                amount_approved: parseInt(amountMatch[1]),
                amount_value: parseInt(amountMatch[1]),
                offer_id: offerIdMatch ? offerIdMatch[1] : `offer_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
                currency: currencyMatch ? currencyMatch[1] : 'USD'
            };
            
            // Add optional fields if found
            if (rateMatch) offer.interest_rate_annual = parseFloat(rateMatch[1]);
            if (durationMatch) offer.repayment_duration_months = parseInt(durationMatch[1]);
            if (statusMatch) offer.status = statusMatch[1];
            if (dateMatch) offer.created_date = dateMatch[1];
            if (esgMatch) offer.esg_impact_summary = esgMatch[1];
            if (statusMsgMatch) offer.status_message = statusMsgMatch[1];
            if (scheduleMatch) offer.repayment_schedule = scheduleMatch[1];
            
            return offer;
        }
        return null;
    }
    
    formatAmount(amount) {
        // Ensure amount is a number
        const numAmount = typeof amount === 'string' ? parseFloat(amount.replace(/,/g, '')) : amount;
        if (isNaN(numAmount)) return '0';
        
        // Format with commas and handle large numbers
        if (numAmount >= 1000000) {
            return (numAmount / 1000000).toFixed(1) + 'M';
        } else if (numAmount >= 1000) {
            return (numAmount / 1000).toFixed(1) + 'K';
        } else {
            return numAmount.toLocaleString();
        }
    }
    
    formatInterestRate(rate) {
        // Ensure rate is a number
        const numRate = typeof rate === 'string' ? parseFloat(rate) : rate;
        if (isNaN(numRate)) return '0.00';
        
        // Format to 2 decimal places
        return numRate.toFixed(2);
    }
    
    showCreditOffersButton() {
        if (this.elements.creditOffersButtonContainer) {
            this.elements.creditOffersButtonContainer.style.display = 'flex';
            
            // Update button text based on number of offers
            const buttonText = this.creditOffers.length > 1 ? 
                `View ${this.creditOffers.length} Offers` : 
                'View Offer';
            this.elements.creditOffersBtn.querySelector('span').textContent = buttonText;
        }
    }
    
    hideCreditOffersButton() {
        if (this.elements.creditOffersButtonContainer) {
            this.elements.creditOffersButtonContainer.style.display = 'none';
        }
        this.hasCreditOffers = false;
        this.creditOffers = [];
    }
    
    showCreditOffersModal() {
        if (this.creditOffers.length === 0) return;
        
        const modal = document.createElement('div');
        modal.className = 'credit-offers-modal';
        modal.id = 'creditOffersModal';
        
        const modalContent = this.creditOffers.length === 1 ? 
            this.generateSingleOfferModal() : 
            this.generateMultipleOffersModal();
        
        modal.innerHTML = modalContent;
        
        // Add to document
        document.body.appendChild(modal);
        
        // Show modal
        modal.style.display = 'flex';
        
        // Add click outside to close
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                this.closeCreditOffersModal();
            }
        });
        
        // Add close button event
        const closeBtn = modal.querySelector('.modal-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                this.closeCreditOffersModal();
            });
        }
    }
    
    generateSingleOfferModal() {
        const offer = this.creditOffers[0];
        
        // Enhanced bank name extraction with better fallbacks
        let bankName = offer.bankid || offer.bankname || offer.bank_name || offer.signer || 'Unknown Bank';
        
        // Clean up bank name - remove "Agent" suffix and standardize
        bankName = bankName.replace(/\s*Agent$/i, '').replace(/_/g, ' ');
        
        // Map internal bank identifiers to proper display names
        const bankNameMap = {
            'bank_agent_1': 'CloudTrust Financial',
            'bank_agent_2': 'Finovate Bank', 
            'bank_agent_3': 'Zentra Bank',
            'bank_agent_4': 'NexVault Bank',
            'bank_agent_5': 'Byte Bank',
            'cloudtrust_financial_agent': 'CloudTrust Financial',
            'finovate_bank_agent': 'Finovate Bank',
            'zentra_bank_agent': 'Zentra Bank',
            'nexvault_bank_agent': 'NexVault Bank',
            'byte_bank_agent': 'Byte Bank'
        };
        
        // Use mapped name if available, otherwise use cleaned name
        bankName = bankNameMap[bankName.toLowerCase()] || bankName;
        
        const bankInitials = bankName.split(' ').map(word => word[0]).join('').substring(0, 2);
        const status = offer.status || 'approved';
        
        // Enhanced amount extraction and formatting
        let amount = offer.amount_approved || offer.amount_value || offer.amount || offer.approved_amount;
        if (typeof amount === 'string') {
            // Remove currency symbols and commas, then parse
            amount = parseFloat(amount.replace(/[$,]/g, ''));
        }
        
        // Enhanced interest rate extraction
        let interestRate = offer.interest_rate_annual || offer.interest_rate || offer.rate || offer.annual_rate;
        if (typeof interestRate === 'string') {
            // Remove percentage symbol if present
            interestRate = parseFloat(interestRate.replace(/%/g, ''));
        }
        
        // Enhanced repayment duration extraction
        let duration = offer.repayment_duration_months || offer.repayment_duration || offer.term || offer.duration_months;
        if (typeof duration === 'string') {
            duration = parseInt(duration);
        }
        
        // Determine modal title and icon based on status
        let modalTitle, modalIcon, statusClass;
        if (status === 'accepted') {
            modalTitle = 'Final Agreed Upon Offer';
            modalIcon = 'fas fa-check-circle';
            statusClass = 'accepted';
        } else if (status === 'rejected') {
            modalTitle = 'Offer Details';
            modalIcon = 'fas fa-times-circle';
            statusClass = 'rejected';
        } else {
            modalTitle = 'Credit Offer Details';
            modalIcon = 'fas fa-university';
            statusClass = 'approved';
        }
        
        // Generate action buttons based on status
        let actionButtons = '';
        if (status === 'accepted') {
            actionButtons = `
                <div class="offer-actions">
                    <button class="btn btn-secondary" onclick="chatApp.closeCreditOffersModal()">Close</button>
                </div>
            `;
        } else if (status === 'rejected') {
            actionButtons = `
                <div class="offer-actions">
                    <button class="btn btn-secondary" onclick="chatApp.closeCreditOffersModal()">Close</button>
                </div>
            `;
        } else {
            actionButtons = `
                <div class="offer-actions">
                    <button class="btn btn-secondary" onclick="chatApp.closeCreditOffersModal()">Close</button>
                    <button class="btn btn-primary" onclick="chatApp.acceptOffer('${offer.offer_id || 'default'}')">Accept Offer</button>
                </div>
            `;
        }
        
        return `
            <div class="credit-offers-modal-content">
                <div class="credit-offers-modal-header">
                    <h3>
                        <i class="${modalIcon}"></i>
                        ${modalTitle}
                    </h3>
                    <button class="modal-close">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="credit-offers-modal-body">
                    <div class="single-offer-card">
                        <div class="offer-header">
                            <div class="bank-info">
                                <div class="bank-logo">${bankInitials}</div>
                                <div class="bank-details">
                                    <h4>${bankName}</h4>
                                    <p>${status === 'accepted' ? 'Final Credit Line Agreement' : 'Credit Line Offer'}</p>
                                </div>
                            </div>
                            <div class="offer-status ${statusClass}">
                                ${status.toUpperCase()}
                            </div>
                        </div>
                        
                        <div class="offer-details-grid">
                            ${amount ? `
                            <div class="offer-detail-item">
                                <div class="offer-detail-label">Credit Amount</div>
                                <div class="offer-detail-value currency">$${this.formatAmount(amount)}</div>
                            </div>
                            ` : ''}
                            ${interestRate ? `
                            <div class="offer-detail-item">
                                <div class="offer-detail-label">Interest Rate (Annual)</div>
                                <div class="offer-detail-value percentage">${this.formatInterestRate(interestRate)}%</div>
                            </div>
                            ` : ''}
                            ${duration ? `
                            <div class="offer-detail-item">
                                <div class="offer-detail-label">Repayment Duration</div>
                                <div class="offer-detail-value">${duration} months</div>
                            </div>
                            ` : ''}
                            ${offer.repayment_schedule ? `
                            <div class="offer-detail-item">
                                <div class="offer-detail-label">Repayment Schedule</div>
                                <div class="offer-detail-value">${offer.repayment_schedule}</div>
                            </div>
                            ` : ''}
                            ${offer.currency ? `
                            <div class="offer-detail-item">
                                <div class="offer-detail-label">Currency</div>
                                <div class="offer-detail-value">${offer.currency}</div>
                            </div>
                            ` : ''}
                            ${offer.created_date ? `
                            <div class="offer-detail-item">
                                <div class="offer-detail-label">Created Date</div>
                                <div class="offer-detail-value">${new Date(offer.created_date).toLocaleDateString()}</div>
                            </div>
                            ` : ''}
                            ${offer.offer_id ? `
                            <div class="offer-detail-item">
                                <div class="offer-detail-label">Offer ID</div>
                                <div class="offer-detail-value">${offer.offer_id}</div>
                            </div>
                            ` : ''}
                            <div class="offer-detail-item">
                                <div class="offer-detail-label">Status</div>
                                <div class="offer-detail-value">${status.toUpperCase()}</div>
                            </div>
                            ${offer.esg_impact_summary || offer.ESG_impact_summary ? `
                            <div class="offer-detail-item full-width">
                                <div class="offer-detail-label">ESG Impact Summary</div>
                                <div class="offer-detail-value">${offer.esg_impact_summary || offer.ESG_impact_summary}</div>
                            </div>
                            ` : ''}
                            ${offer.status_message ? `
                            <div class="offer-detail-item full-width">
                                <div class="offer-detail-label">Status Message</div>
                                <div class="offer-detail-value">${offer.status_message}</div>
                            </div>
                            ` : ''}
                        </div>
                        
                        ${actionButtons}
                    </div>
                </div>
            </div>
        `;
    }
    
    generateMultipleOffersModal() {
        // Check if all offers are accepted or rejected
        const allAccepted = this.creditOffers.every(offer => offer.status === 'accepted');
        const allRejected = this.creditOffers.every(offer => offer.status === 'rejected');
        const hasRejected = this.creditOffers.some(offer => offer.status === 'rejected');
        
        let modalTitle, modalIcon;
        if (allAccepted) {
            modalTitle = 'Final Agreed Upon Offers';
            modalIcon = 'fas fa-check-circle';
        } else if (hasRejected) {
            modalTitle = 'Credit Offers Comparison';
            modalIcon = 'fas fa-chart-line';
        } else {
            modalTitle = 'Credit Offers Comparison';
            modalIcon = 'fas fa-chart-line';
        }
        
        return `
            <div class="credit-offers-modal-content">
                <div class="credit-offers-modal-header">
                    <h3>
                        <i class="${modalIcon}"></i>
                        ${modalTitle}
                    </h3>
                    <button class="modal-close">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="credit-offers-modal-body">
                    <div class="offers-table-container">
                        <table class="offers-table">
                            <thead>
                                <tr>
                                    <th>Bank</th>
                                    <th>Credit Amount</th>
                                    <th>Interest Rate</th>
                                    <th>Term</th>
                                    <th>Status</th>
                                    ${!allAccepted && !hasRejected ? '<th>Actions</th>' : ''}
                                </tr>
                            </thead>
                            <tbody>
                                ${this.creditOffers.map(offer => {
                                    // Enhanced bank name extraction with same logic as single offer
                                    let bankName = offer.bankid || offer.bankname || offer.bank_name || offer.signer || 'Unknown Bank';
                                    
                                    // Clean up bank name - remove "Agent" suffix and standardize
                                    bankName = bankName.replace(/\s*Agent$/i, '').replace(/_/g, ' ');
                                    
                                    // Map internal bank identifiers to proper display names
                                    const bankNameMap = {
                                        'bank_agent_1': 'CloudTrust Financial',
                                        'bank_agent_2': 'Finovate Bank', 
                                        'bank_agent_3': 'Zentra Bank',
                                        'bank_agent_4': 'NexVault Bank',
                                        'bank_agent_5': 'Byte Bank',
                                        'cloudtrust_financial_agent': 'CloudTrust Financial',
                                        'finovate_bank_agent': 'Finovate Bank',
                                        'zentra_bank_agent': 'Zentra Bank',
                                        'nexvault_bank_agent': 'NexVault Bank',
                                        'byte_bank_agent': 'Byte Bank'
                                    };
                                    
                                    // Use mapped name if available, otherwise use cleaned name
                                    bankName = bankNameMap[bankName.toLowerCase()] || bankName;
                                    
                                    const bankInitials = bankName.split(' ').map(word => word[0]).join('').substring(0, 2);
                                    const status = offer.status || 'approved';
                                    
                                    // Enhanced amount extraction
                                    let amount = offer.amount_approved || offer.amount_value || offer.amount || offer.approved_amount;
                                    if (typeof amount === 'string') {
                                        amount = parseFloat(amount.replace(/[$,]/g, ''));
                                    }
                                    
                                    // Enhanced interest rate extraction
                                    let interestRate = offer.interest_rate_annual || offer.interest_rate || offer.rate || offer.annual_rate;
                                    if (typeof interestRate === 'string') {
                                        interestRate = parseFloat(interestRate.replace(/%/g, ''));
                                    }
                                    
                                    // Enhanced repayment duration extraction
                                    let duration = offer.repayment_duration_months || offer.repayment_duration || offer.term || offer.duration_months;
                                    if (typeof duration === 'string') {
                                        duration = parseInt(duration);
                                    }
                                    
                                    let actionButton = '';
                                    if (status === 'approved' && !allAccepted && !hasRejected) {
                                        actionButton = `
                                            <td>
                                                <button class="btn btn-primary" onclick="chatApp.acceptOffer('${offer.offer_id || 'default'}')">
                                                    Accept
                                                </button>
                                            </td>
                                        `;
                                    } else if (!allAccepted && !hasRejected) {
                                        actionButton = '<td></td>';
                                    }
                                    
                                    return `
                                        <tr>
                                            <td class="bank-cell">
                                                <div class="bank-logo">${bankInitials}</div>
                                                <span>${bankName}</span>
                                            </td>
                                            <td class="amount-cell">${amount ? `$${this.formatAmount(amount)}` : 'N/A'}</td>
                                            <td class="rate-cell">${interestRate ? `${this.formatInterestRate(interestRate)}%` : 'N/A'}</td>
                                            <td>${duration ? `${duration} months` : 'N/A'}</td>
                                            <td class="status-cell">
                                                <span class="offer-status ${status}">
                                                    ${status.toUpperCase()}
                                                </span>
                                            </td>
                                            ${actionButton}
                                        </tr>
                                    `;
                                }).join('')}
                            </tbody>
                        </table>
                    </div>
                    
                    <div class="offer-actions" style="margin-top: var(--space-lg);">
                        <button class="btn btn-secondary" onclick="chatApp.closeCreditOffersModal()">Close</button>
                    </div>
                </div>
            </div>
        `;
    }
    
    closeCreditOffersModal() {
        const modal = document.getElementById('creditOffersModal');
        if (modal) {
            modal.remove();
        }
    }
    
    acceptOffer(offerId) {
        // Add a message to the chat about accepting the offer
        const offer = this.creditOffers.find(o => o.offer_id === offerId);
        const bankName = offer ? offer.bankid : 'the bank';
        
        const acceptanceMessage = `I would like to accept the credit offer from ${bankName}. Please proceed with the acceptance process.`;
        
        // Set the message in the input field
        this.elements.messageInput.value = acceptanceMessage;
        
        // Close the modal first
        this.closeCreditOffersModal();
        
        // Hide the offers button
        this.hideCreditOffersButton();
        
        // Send the message directly
        this.sendMessage();
    }
    
    mapBackendOfferToFrontend(offerData, bankName) {
        try {
            // Handle different backend offer structures and map to consistent frontend format
            const mappedOffer = {
                // Bank identification
                bankid: bankName || offerData.bank?.bank_name || offerData.bankid || offerData.bankname,
                
                // Amount fields - try multiple possible field names from backend
                amount_approved: offerData.offer_terms?.approved_amount || 
                                offerData.approved_amount || 
                                offerData.amount_approved || 
                                offerData.amount_value ||
                                offerData.amount,
                                
                amount_value: offerData.offer_terms?.approved_amount || 
                             offerData.approved_amount || 
                             offerData.amount_approved || 
                             offerData.amount_value ||
                             offerData.amount,
                
                // Interest rate fields
                interest_rate_annual: offerData.offer_terms?.interest_rate || 
                                     offerData.interest_rate_annual ||
                                     offerData.interest_rate ||
                                     offerData.rate,
                
                // Repayment duration fields
                repayment_duration_months: offerData.offer_terms?.repayment_period || 
                                          offerData.repayment_duration_months ||
                                          offerData.repayment_duration ||
                                          offerData.term,
                
                repayment_duration: offerData.offer_terms?.repayment_period || 
                                   offerData.repayment_duration_months ||
                                   offerData.repayment_duration ||
                                   offerData.term,
                
                // Additional offer details
                currency: offerData.currency || 'USD',
                offer_id: offerData.offer_id || `offer_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
                
                // Optional fields
                origination_fee: offerData.offer_terms?.origination_fee || offerData.origination_fee,
                annual_fee: offerData.offer_terms?.annual_fee || offerData.annual_fee,
                drawing_period: offerData.offer_terms?.drawing_period || offerData.drawing_period,
                
                // ESG information
                esg_impact_summary: offerData.esg_impact?.esg_summary || offerData.esg_impact_summary,
                carbon_footprint: offerData.esg_impact?.carbon_footprint || offerData.carbon_footprint,
                esg_score: offerData.esg_impact?.esg_score || offerData.esg_score,
                
                // Status and metadata
                status: offerData.status || offerData.approval_status || 'approved',
                created_date: offerData.created_date || offerData.timestamp || new Date().toISOString(),
                
                // Compliance and verification
                signature_verified: offerData.signature_verified || false,
                
                // Additional details that might be present
                repayment_schedule: offerData.repayment_schedule,
                collateral_required: offerData.collateral_required,
                status_message: offerData.status_message || offerData.message
            };
            
            // Remove undefined/null values to keep the object clean
            Object.keys(mappedOffer).forEach(key => {
                if (mappedOffer[key] === undefined || mappedOffer[key] === null) {
                    delete mappedOffer[key];
                }
            });
            
            console.log('Mapped backend offer:', offerData, 'to frontend format:', mappedOffer);
            return mappedOffer;
            
        } catch (error) {
            console.error('Error mapping backend offer to frontend:', error, offerData);
            return null;
        }
    }
}

// Utility functions for UI interactions
function showInformationHelp() {
    const helpContent = `
        <h4>Credit Line Information & Guidance</h4>
        
        <div style="margin: var(--space-lg) 0;">
            <h5><i class="fas fa-university" style="color: var(--primary-color);"></i> What We Offer</h5>
            <p>Our A2A Consumer Bank system connects you with 3 partner banks to find the best credit line offers:</p>
            <ul>
                <li><strong>CloudTrust Financial</strong> - ESG-focused lending with competitive rates</li>
                <li><strong>Finovate Bank</strong> - Flexible terms and fast processing</li>
                <li><strong>Zentra Bank</strong> - Specialists in business expansion loans</li>
                <li><strong>Byte Bank</strong> - ESG-focused lending with competitive rates</li>
                <li><strong>NexVault Bank</strong> - Flexible terms and fast processing</li>
            </ul>
        </div>
        
        <div style="margin: var(--space-lg) 0;">
            <h5><i class="fas fa-clipboard-list" style="color: var(--primary-color);"></i> Application Requirements</h5>
            <ul>
                <li><strong>Purpose:</strong> Working capital, equipment, expansion, etc.</li>
                <li><strong>Amount:</strong> Credit line amount needed</li>
                <li><strong>Duration:</strong> Preferred repayment period</li>
                <li><strong>Interest Rate:</strong> Your target rate</li>
                <li><strong>Collateral:</strong> Assets for security (if any)</li>
                <li><strong>ESG Info:</strong> Environmental/social governance details</li>
            </ul>
        </div>
        
        <div style="margin: var(--space-lg) 0;">
            <h5><i class="fas fa-cogs" style="color: var(--primary-color);"></i> How It Works</h5>
            <ol>
                <li>Submit your credit requirements</li>
                <li>System contacts all 3 banks simultaneously</li>
                <li>Receive and compare multiple offers</li>
                <li>Negotiate terms with preferred banks</li>
                <li>Select and accept the best offer</li>
            </ol>
        </div>
        
        <div class="form-actions">
            <button type="button" class="btn btn-primary" onclick="closeModal()">Got it!</button>
        </div>
    `;
    
    chatApp.showModal('Credit Services Information', helpContent);
}

function showADKInfo() {
    const adkContent = `
        <h4>Using ADK Web Interface</h4>
        
        <div style="background: var(--bg-secondary); padding: var(--space-lg); border-radius: var(--radius-md); margin: var(--space-lg) 0;">
            <h5 style="color: var(--success-color);">✅ Recommended for Full Functionality</h5>
            <p>The ADK Web Interface provides complete access to all ConsumerAgent capabilities without compatibility issues.</p>
        </div>
        
        <div style="margin: var(--space-lg) 0;">
            <h5><i class="fas fa-rocket" style="color: var(--primary-color);"></i> How to Access ADK Web</h5>
            <ol>
                <li>Ensure your ConsumerAgent is running</li>
                <li>Open a web browser</li>
                <li>Navigate to the ADK web interface (typically provided by the ADK framework)</li>
                <li>Connect to your ConsumerAgent</li>
                <li>Use the full credit application functionality</li>
            </ol>
        </div>
        
        <div style="margin: var(--space-lg) 0;">
            <h5><i class="fas fa-star" style="color: var(--primary-color);"></i> ADK Web Advantages</h5>
            <ul>
                <li><strong>Full Tool Access:</strong> All agent tools work perfectly</li>
                <li><strong>Real Processing:</strong> Complete credit applications</li>
                <li><strong>Bank Integration:</strong> Direct communication with all partner banks</li>
                <li><strong>Proven Reliability:</strong> Standard ADK interface</li>
            </ul>
        </div>
        
        <div style="margin: var(--space-lg) 0;">
            <h5><i class="fas fa-info-circle" style="color: var(--primary-color);"></i> This Custom Interface</h5>
            <p>Currently best used for:</p>
            <ul>
                <li>Learning about credit services</li>
                <li>Understanding application requirements</li>
                <li>Getting guidance and information</li>
                <li>Exploring the process before applying</li>
            </ul>
        </div>
        
        <div class="form-actions">
            <button type="button" class="btn btn-primary" onclick="closeModal()">Understood</button>
        </div>
    `;
    
    chatApp.showModal('ADK Web Interface Guide', adkContent);
}

function startCreditApplication() {
    const formContent = `
        <form id="creditApplicationForm">
            <div class="form-group">
                <label for="purpose">Purpose of Credit Line *</label>
                <textarea id="purpose" required placeholder="Describe the purpose of your credit line (e.g., working capital, equipment purchase, business expansion, inventory financing, etc.)"></textarea>
            </div>
            
            <div class="form-group">
                <label for="amount">Requested Amount (USD) *</label>
                <input type="number" id="amount" min="10000" max="10000000" step="1000" required placeholder="e.g., 500000">
            </div>
            
            <div class="form-group">
                <label for="duration">Repayment Duration (months) *</label>
                <input type="number" id="duration" min="6" max="60" required placeholder="e.g., 24">
            </div>
            
            <div class="form-group">
                <label for="preferredRate">Preferred Interest Rate (%) *</label>
                <input type="number" id="preferredRate" min="1" max="25" step="0.1" required placeholder="e.g., 8.5">
            </div>
            
            <div class="form-group">
                <label for="repaymentType">Repayment Preference *</label>
                <select id="repaymentType" required>
                    <option value="">Select type...</option>
                    <option value="monthly">Monthly</option>
                    <option value="quarterly">Quarterly</option>
                    <option value="semi-annual">Semi-Annual</option>
                    <option value="annual">Annual</option>
                </select>
            </div>
            
            <div class="form-group">
                <label for="senderContactEmail">Contact Email *</label>
                <input type="email" id="senderContactEmail" required placeholder="e.g., finance@company.com">
            </div>
            
            <div class="form-group">
                <label for="drawdownType">Drawdown Type *</label>
                <select id="drawdownType" required>
                    <option value="">Select drawdown type...</option>
                    <option value="partial">Partial</option>
                    <option value="lump-sum">Lump-Sum</option>
                    <option value="revolving">Revolving</option>
                </select>
            </div>
            
            <div class="form-group">
                <label for="collateral">Collateral Description</label>
                <textarea id="collateral" placeholder="Describe any collateral you can offer (optional)"></textarea>
            </div>
            
            <div class="form-group">
                <label for="esgConsent">
                    <input type="checkbox" id="esgConsent" checked>
                    I consent to ESG (Environmental, Social, Governance) assessment and reporting
                </label>
            </div>
            
            <div class="form-actions">
                <button type="button" class="btn btn-secondary" onclick="closeModal()">Cancel</button>
                <button type="submit" class="btn btn-primary">Submit Application</button>
            </div>
        </form>
    `;
    
    chatApp.showModal('Credit Line Application', formContent);
    
    // Handle form submission
    document.getElementById('creditApplicationForm').addEventListener('submit', (e) => {
        e.preventDefault();
        
        const formData = {
            purpose: document.getElementById('purpose').value,
            amount_value: parseInt(document.getElementById('amount').value),
            repayment_duration: parseInt(document.getElementById('duration').value),
            preferred_interest_rate: parseFloat(document.getElementById('preferredRate').value),
            repayment_preference: document.getElementById('repaymentType').value,
            sender_contact_email: document.getElementById('senderContactEmail').value,
            drawdown_type: document.getElementById('drawdownType').value,
            collateral_description: document.getElementById('collateral').value,
            data_sharing_consent: document.getElementById('esgConsent').checked
        };
        
        chatApp.closeModal();
        
        // Create a structured message for the ConsumerAgent
        const message = `I would like to apply for a credit line with the following details:

**Purpose**: ${formData.purpose}
**Amount**: $${formData.amount_value.toLocaleString()}
**Repayment Duration**: ${formData.repayment_duration} months
**Preferred Interest Rate**: ${formData.preferred_interest_rate}%
**Repayment Preference**: ${formData.repayment_preference}
**Contact Email**: ${formData.sender_contact_email}
**Drawdown Type**: ${formData.drawdown_type}
**Collateral**: ${formData.collateral_description || 'None specified'}
**ESG Consent**: ${formData.data_sharing_consent ? 'Yes' : 'No'}

Please process this application using the build_and_send_credit_request tool and get quotes from all available bank agents.`;
        
        // Add message to chat and process
        chatApp.elements.messageInput.value = message;
        chatApp.sendMessage();
    });
}

function showSampleRequest() {
    const sampleContent = `
        <h4>Sample Credit Line Request</h4>
        <p>Here's a comprehensive example showing all the fields from our credit application form:</p>
        
        <div style="background: var(--bg-secondary); padding: var(--space-lg); border-radius: var(--radius-md); margin: var(--space-lg) 0;">
            <h5 style="color: var(--primary-color); margin-bottom: var(--space-md);">Complete Sample Application</h5>
            <p><strong>Purpose:</strong> Working capital for seasonal inventory expansion and equipment upgrades to support increased demand during Q4 holiday season</p>
            <p><strong>Requested Amount:</strong> $750,000 USD</p>
            <p><strong>Repayment Duration:</strong> 18 months</p>
            <p><strong>Preferred Interest Rate:</strong> 7.5% annual</p>
            <p><strong>Repayment Preference:</strong> Monthly installments</p>
            <p><strong>Contact Email:</strong> finance@sunshinemedical.com</p>
            <p><strong>Drawdown Type:</strong> Revolving (allows multiple withdrawals)</p>
            <p><strong>Collateral:</strong> Accounts receivable ($400K), inventory assets ($300K), and medical equipment ($200K)</p>
            <p><strong>ESG Consent:</strong> Yes - Company commits to ESG reporting and has ISO26000, ENERGY STAR, and LEED certifications</p>
        </div>
        
        <div style="margin: var(--space-lg) 0;">
            <h5>Additional Sample Scenarios:</h5>
            
            <div style="background: var(--bg-tertiary); padding: var(--space-md); border-radius: var(--radius-sm); margin: var(--space-md) 0;">
                <strong>Equipment Financing:</strong><br>
                Purpose: New manufacturing equipment purchase<br>
                Amount: $1,200,000 | Duration: 36 months | Rate: 6.8%<br>
                Repayment: Quarterly | Drawdown: Lump-Sum<br>
                Collateral: Equipment being financed
            </div>
            
            <div style="background: var (--bg-tertiary); padding: var(--space-md); border-radius: var(--radius-sm); margin: var(--space-md) 0;">
                <strong>Business Expansion:</strong><br>
                Purpose: Market expansion and facility construction<br>
                Amount: $2,500,000 | Duration: 48 months | Rate: 8.2%<br>
                Repayment: Semi-Annual | Drawdown: Partial<br>
                Collateral: Real estate and business assets
            </div>
        </div>
        
        <div style="background: var(--bg-warning); padding: var(--space-md); border-radius: var(--radius-sm); margin: var(--space-lg) 0;">
            <h5 style="color: var(--warning-color);"><i class="fas fa-lightbulb"></i> Pro Tips:</h5>
            <ul style="margin: var(--space-sm) 0;">
                <li><strong>Purpose:</strong> Be specific about how funds will be used</li>
                <li><strong>Amount:</strong> Request realistic amounts based on your financials</li>
                <li><strong>Collateral:</strong> Detailed descriptions help banks assess risk</li>
                <li><strong>ESG:</strong> Strong ESG profile can lead to better interest rates</li>
                <li><strong>Drawdown Types:</strong>
                    <ul>
                        <li>Revolving: Access funds multiple times as needed</li>
                        <li>Lump-Sum: Receive full amount at once</li>
                        <li>Partial: Staged withdrawals based on milestones</li>
                    </ul>
                </li>
            </ul>
        </div>
        
        <p>You can either use the structured form or simply describe your needs in natural language. The AI assistant will help format and process your request with all required fields.</p>
        
        <div class="form-actions">
            <button type="button" class="btn btn-secondary" onclick="closeModal()">Close</button>
            <button type="button" class="btn btn-primary" onclick="closeModal(); startCreditApplication();">Start My Application</button>
        </div>
    `;
    
    chatApp.showModal('Sample Credit Request', sampleContent);
}

function showHelp() {
    const helpContent = `
        <h4>How to Use the Credit Line Assistant</h4>
        
        <div style="margin: var(--space-lg) 0;">
            <h5><i class="fas fa-play-circle" style="color: var(--primary-color);"></i> Getting Started</h5>
            <ul>
                <li>Click "Start Credit Application" for a guided form</li>
                <li>Or simply type your requirements in natural language</li>
                <li>I'll help you format and submit your request</li>
            </ul>
        </div>
        
        <div style="margin: var(--space-lg) 0;">
            <h5><i class="fas fa-cogs" style="color: var(--primary-color);"></i> Application Process</h5>
            <ol>
                <li><strong>Submit Request:</strong> Provide your credit requirements</li>
                <li><strong>Bank Outreach:</strong> I'll contact all partner banks</li>
                <li><strong>Offer Collection:</strong> Receive and compare multiple offers</li>
                <li><strong>Analysis:</strong> Get recommendations based on your criteria</li>
                <li><strong>Negotiation:</strong> Improve terms with specific banks</li>
                <li><strong>Selection:</strong> Choose and accept the best offer</li>
            </ol>
        </div>
        
        <div style="margin: var(--space-lg) 0;">
            <h5><i class="fas fa-lightbulb" style="color: var(--primary-color);"></i> Tips for Best Results</h5>
            <ul>
                <li>Provide complete information upfront</li>
                <li>Be specific about your preferences</li>
                <li>Consider ESG factors for better rates</li>
                <li>Review all offers before deciding</li>
            </ul>
        </div>
        
        <div class="form-actions">
            <button type="button" class="btn btn-primary" onclick="closeModal()">Got it!</button>
        </div>
    `;
    
    chatApp.showModal('Help & Instructions', helpContent);
}

function showSampleRequests() {
    const samplesContent = `
        <h4>Sample Request Templates</h4>
        
        <div style="margin: var(--space-lg) 0;">
            <h5>Working Capital Request</h5>
            <div style="background: var(--bg-secondary); padding: var(--space-md); border-radius: var (--radius-md); font-family: monospace; font-size: var(--font-size-sm);">
"I need $500,000 for working capital to support seasonal operations. Looking for 24-month repayment with monthly installments. Preferred rate under 8%. Can offer accounts receivable as collateral."
            </div>
        </div>
        
        <div style="margin: var(--space-lg) 0;">
            <h5>Equipment Financing</h5>
            <div style="background: var(--bg-secondary); padding: var(--space-md); border-radius: var(--radius-md); font-family: monospace; font-size: var(--font-size-sm);">
"Need $1.2M credit line for new manufacturing equipment. 36-month term preferred. Equipment will serve as collateral. Company has strong ESG profile with LEED certification."
            </div>
        </div>
        
        <div style="margin: var(--space-lg) 0;">
            <h5>Business Expansion</h5>
            <div style="background: var(--bg-secondary); padding: var(--space-md); border-radius: var(--radius-md); font-family: monospace; font-size: var(--font-size-sm);">
"Looking for $2M line of credit for market expansion. 48-month repayment, quarterly payments preferred. Rate flexibility for faster approval. Expansion will create 50+ jobs."
            </div>
        </div>
        
        <div class="form-actions">
            <button type="button" class="btn btn-secondary" onclick="closeModal()">Close</button>
            <button type="button" class="btn btn-primary" onclick="closeModal(); startCreditApplication();">Use Template</button>
        </div>
    `;
    
    chatApp.showModal('Sample Requests', samplesContent);
}

function showAPIInfo() {
    const apiContent = `
        <h4>API Integration Information</h4>
        
        <div style="margin: var (--space-lg) 0;">
            <h5><i class="fas fa-server" style="color: var(--primary-color);"></i> Host Agent Endpoint</h5>
            <p>The chat interface communicates with the host agent through streaming API:</p>
            <div style="background: var(--bg-secondary); padding: var(--space-md); border-radius: var(--radius-md); font-family: monospace; font-size: var(--font-size-sm);">
POST /stream<br>
Content-Type: application/json<br><br>
{<br>
&nbsp;&nbsp;"query": "user message",<br>
&nbsp;&nbsp;"session_id": "unique_session_id"<br>
}
            </div>
        </div>
        
        <div style="margin: var(--space-lg) 0;">
            <h5><i class="fas fa-network-wired" style="color: var(--primary-color);"></i> Bank Agent Connections</h5>
            <ul>
                <li><strong>CloudTrust Financial:</strong> localhost:10002</li>
                <li><strong>Finovate Bank:</strong> localhost:10003</li>
                <li><strong>Zentra Bank:</strong> localhost:10004</li>
                <li><strong>Byte Bank:</strong> localhost:10005</li>
                <li><strong>NexVault Bank:</strong> localhost:10006</li>
            </ul>
        </div>
        
        <div style="margin: var(--space-lg) 0;">
            <h5><i class="fas fa-exchange-alt" style="color: var(--primary-color);"></i> Message Flow</h5>
            <ol>
                <li>User input → Custom UI</li>
                <li>Custom UI → Host Agent (Consumer Agent)</li>
                <li>Host Agent → Bank Agents (parallel requests)</li>
                <li>Bank Agents → Host Agent (offers/responses)</li>
                <li>Host Agent → Custom UI (formatted response)</li>
            </ol>
        </div>
        
        <div class="form-actions">
            <button type="button" class="btn btn-primary" onclick="closeModal()">Close</button>
        </div>
    `;
    
    chatApp.showModal('API Information', apiContent);
}

function closeModal() {
    chatApp.closeModal();
}

// Global function to close profile modal
function closeProfileModal() {
    if (chatApp) {
        chatApp.closeProfileModal();
    }
}

// Initialize the chat application when DOM is loaded
let chatApp;
document.addEventListener('DOMContentLoaded', () => {
    chatApp = new ChatApp();
});

// Test function for credit offers popup (can be called from browser console)
function testCreditOffersPopup() {
    if (chatApp) {
        // Simulate receiving credit offers
        chatApp.creditOffers = [
            {
                bankid: 'CloudTrust Financial',
                amount_value: 500000,
                interest_rate_annual: 7.5,
                offer_id: 'offer_ct_001',
                status: 'approved',
                repayment_duration: 24,
                collateral_required: 'Accounts receivable'
            },
            {
                bankid: 'Finovate Bank',
                amount_value: 500000,
                interest_rate_annual: 8.2,
                offer_id: 'offer_fb_001',
                status: 'approved',
                repayment_duration: 24,
                collateral_required: 'Business assets'
            },
            {
                bankid: 'Zentra Bank',
                amount_value: 500000,
                interest_rate_annual: 7.8,
                offer_id: 'offer_zb_001',
                status: 'approved',
                repayment_duration: 24,
                collateral_required: 'Equipment and inventory'
            }
        ];
        chatApp.hasCreditOffers = true;
        chatApp.showCreditOffersButton();
        
        console.log('Credit offers popup test activated! Click the "View 3 Offers" button to see the popup.');
    }
}

// Test function for single offer popup
function testSingleOfferPopup() {
    if (chatApp) {
        chatApp.creditOffers = [
            {
                bankid: 'CloudTrust Financial',
                amount_value: 750000,
                interest_rate_annual: 6.8,
                offer_id: 'offer_ct_002',
                status: 'approved',
                repayment_duration: 36,
                collateral_required: 'Real estate and business assets'
            }
        ];
        chatApp.hasCreditOffers = true;
        chatApp.showCreditOffersButton();
        
        console.log('Single offer popup test activated! Click the "View Offer" button to see the popup.');
    }
}

// Handle system theme changes
if (window.matchMedia) {
    window.matchMedia('(prefers-color-scheme: dark)').addListener(() => {
        if (chatApp && chatApp.settings.theme === 'auto') {
            chatApp.applyTheme();
        }
    });
}
