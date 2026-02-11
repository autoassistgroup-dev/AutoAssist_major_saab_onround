/**
 * Real-Time WebSocket Manager for AutoAssist Portal
 * 
 * Provides centralized WebSocket connection management and event handling
 * for all ticket operations across the application.
 * 
 * Usage:
 *   <script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>
 *   <script src="/static/js/socket-manager.js"></script>
 *   <script>
 *     const socketManager = new SocketManager();
 *     socketManager.on('ticket_forwarded', (data) => { ... });
 *   </script>
 * 
 * Author: AutoAssistGroup Development Team
 */

class SocketManager {
    constructor(options = {}) {
        this.options = {
            autoConnect: true,
            debug: true, // Force debug on for diagnosis
            reconnectionAttempts: 10,
            reconnectionDelay: 1000,
            userId: null,
            role: null,
            ...options
        };

        this.socket = null;
        this.connected = false;
        this.rooms = {
            dashboard: false,
            userRoom: false,
            roleRoom: false,
            ticketRooms: new Set()
        };

        // Event handlers registry
        this.handlers = {};

        // Notification sound
        this.notificationSound = null;
        this.soundEnabled = true;

        if (this.options.autoConnect) {
            this.connect();
        }
    }

    /**
     * Initialize Socket.IO connection
     */
    connect() {
        if (this.socket && this.socket.connected) {
            this._log('Already connected');
            return this;
        }

        this.socket = io({
            transports: ['websocket', 'polling'],
            reconnection: true,
            reconnectionAttempts: this.options.reconnectionAttempts,
            reconnectionDelay: this.options.reconnectionDelay,
            timeout: 10000
        });

        this._setupCoreHandlers();
        return this;
    }

    /**
     * Disconnect from server
     */
    disconnect() {
        if (this.socket) {
            this.socket.disconnect();
            this.connected = false;
        }
        return this;
    }

    /**
     * Setup core connection event handlers
     */
    _setupCoreHandlers() {
        this.socket.on('connect', () => {
            this._log('Connected to server');
            this.connected = true;

            // Auto-join rooms on connect
            this._rejoinRooms();

            // Trigger custom connect handler
            this._emit('connected', { status: 'connected' });
        });

        this.socket.on('disconnect', (reason) => {
            this._log('Disconnected:', reason);
            this.connected = false;
            this._emit('disconnected', { reason });
        });

        this.socket.on('connect_error', (error) => {
            this._log('Connection error:', error.message);
            this._emit('connection_error', { error: error.message });
        });

        // Room join confirmations
        this.socket.on('joined_dashboard', (data) => {
            this._log('Joined dashboard room');
            this.rooms.dashboard = true;
        });

        this.socket.on('joined_user_room', (data) => {
            this._log('Joined user room:', data.room);
            this.rooms.userRoom = data.room;
        });

        this.socket.on('joined_role_room', (data) => {
            this._log('Joined role room:', data.room);
            this.rooms.roleRoom = data.room;
        });

        this.socket.on('joined_ticket', (data) => {
            this._log('Joined ticket room:', data.ticket_id);
            this.rooms.ticketRooms.add(data.ticket_id);
        });

        // Setup all ticket event handlers
        this._setupTicketEventHandlers();
    }

    /**
     * Setup handlers for all ticket-related events
     */
    _setupTicketEventHandlers() {
        const ticketEvents = [
            // Core events
            'new_ticket',
            'new_reply',
            'ticket_updated',
            'reply_sent',

            // Forwarding events
            'ticket_forwarded',
            'ticket_forwarded_to_you',

            // Takeover events
            'ticket_taken_over',
            'ticket_reassigned',

            // Assignment events
            'technician_assigned',

            // Status/Priority events
            'ticket_status_changed',
            'ticket_priority_changed',

            // Bookmark events
            'ticket_bookmarked',

            // Tech Director events
            'ticket_referred',
            'ticket_referred_to_director',
            'ticket_referred_to_you',

            // Typing indicators
            'typing',
            'stop_typing'
        ];

        ticketEvents.forEach(event => {
            this.socket.on(event, (data) => {
                this._log(`Event received: ${event}`, data);
                this._emit(event, data);
            });
        });
    }

    /**
     * Rejoin rooms after reconnection
     */
    _rejoinRooms() {
        // Always join dashboard
        this.joinDashboard();

        // Join user-specific room if authenticated
        this.joinUserRoom();

        // Join role-based room
        this.joinRoleRoom();

        // Rejoin any ticket rooms
        this.rooms.ticketRooms.forEach(ticketId => {
            this.joinTicket(ticketId);
        });
    }

    /**
     * Join the dashboard room for general updates
     */
    joinDashboard() {
        if (!this.socket) return this;
        this.socket.emit('join_dashboard');
        return this;
    }

    /**
     * Join user-specific room for targeted notifications
     */
    joinUserRoom() {
        if (!this.socket) return this;
        // Explicitly pass userId if available, fallback to session on backend
        const data = this.options.userId ? { user_id: this.options.userId } : {};
        this.socket.emit('join_user_room', data);
        return this;
    }

    /**
     * Join role-based room for role-specific notifications
     * @param {string} role - Optional role override
     */
    joinRoleRoom(role = null) {
        if (!this.socket) return this;
        // Use passed role, or instance option role, or fallback to session
        const targetRole = role || this.options.role;
        const data = targetRole ? { role: targetRole } : {};
        this.socket.emit('join_role_room', data);
        return this;
    }

    /**
     * Join a specific ticket room for live updates
     * @param {string} ticketId - The ticket ID to join
     */
    joinTicket(ticketId) {
        if (!this.socket || !ticketId) return this;
        this.socket.emit('join_ticket', { ticket_id: ticketId });
        this.rooms.ticketRooms.add(ticketId);
        return this;
    }

    /**
     * Leave a specific ticket room
     * @param {string} ticketId - The ticket ID to leave
     */
    leaveTicket(ticketId) {
        if (!this.socket || !ticketId) return this;
        this.socket.emit('leave_ticket', { ticket_id: ticketId });
        this.rooms.ticketRooms.delete(ticketId);
        return this;
    }

    /**
     * Send typing indicator
     * @param {string} ticketId - The ticket being typed on
     * @param {string} userName - The user's name
     */
    sendTyping(ticketId, userName) {
        if (!this.socket) return this;
        this.socket.emit('typing', {
            ticket_id: ticketId,
            user_name: userName
        });
        return this;
    }

    /**
     * Send stop typing indicator
     * @param {string} ticketId - The ticket ID
     */
    sendStopTyping(ticketId) {
        if (!this.socket) return this;
        this.socket.emit('stop_typing', { ticket_id: ticketId });
        return this;
    }

    /**
     * Register an event handler
     * @param {string} event - Event name
     * @param {function} handler - Handler function
     */
    on(event, handler) {
        if (!this.handlers[event]) {
            this.handlers[event] = [];
        }
        this.handlers[event].push(handler);
        return this;
    }

    /**
     * Remove an event handler
     * @param {string} event - Event name
     * @param {function} handler - Handler function (optional, removes all if not provided)
     */
    off(event, handler = null) {
        if (!this.handlers[event]) return this;

        if (handler) {
            this.handlers[event] = this.handlers[event].filter(h => h !== handler);
        } else {
            delete this.handlers[event];
        }
        return this;
    }

    /**
     * Emit event to registered handlers
     * @private
     */
    _emit(event, data) {
        const handlers = this.handlers[event] || [];
        handlers.forEach(handler => {
            try {
                handler(data);
            } catch (error) {
                console.error(`Error in ${event} handler:`, error);
            }
        });
    }

    /**
     * Debug logging
     * @private
     */
    _log(...args) {
        if (this.options.debug) {
            console.log('[SocketManager]', ...args);
        }
    }

    /**
     * Play notification sound
     */
    playNotificationSound() {
        if (!this.soundEnabled) return;

        if (!this.notificationSound) {
            this.notificationSound = new Audio('https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3');
            this.notificationSound.volume = 0.5;
        }

        this.notificationSound.play().catch(err => {
            this._log('Could not play notification sound:', err);
        });
    }

    /**
     * Enable/disable notification sounds
     * @param {boolean} enabled 
     */
    setSoundEnabled(enabled) {
        this.soundEnabled = enabled;
        return this;
    }

    /**
     * Show browser notification if permitted
     * @param {string} title - Notification title
     * @param {object} options - Notification options (body, icon, etc.)
     */
    showNotification(title, options = {}) {
        if (!('Notification' in window)) return;

        if (Notification.permission === 'granted') {
            new Notification(title, options);
        } else if (Notification.permission !== 'denied') {
            Notification.requestPermission().then(permission => {
                if (permission === 'granted') {
                    new Notification(title, options);
                }
            });
        }
    }

    /**
     * Check if connected
     * @returns {boolean}
     */
    isConnected() {
        return this.connected && this.socket && this.socket.connected;
    }
}


// ============== UI Update Helpers ==============

/**
 * Helper functions for updating ticket UI elements in real-time
 */
const TicketUIUpdater = {
    /**
     * Update ticket status badge
     * @param {string} ticketId - Ticket ID
     * @param {string} newStatus - New status value
     */
    updateStatus(ticketId, newStatus) {
        // Update in ticket list
        const ticketCard = document.querySelector(`[data-ticket-id="${ticketId}"]`);
        if (ticketCard) {
            const statusBadge = ticketCard.querySelector('.ticket-status, [data-status]');
            if (statusBadge) {
                statusBadge.textContent = newStatus;
                statusBadge.className = statusBadge.className.replace(/status-\w+/g, '');
                statusBadge.classList.add(`status-${newStatus.toLowerCase().replace(/\s+/g, '-')}`);
            }
        }

        // Update in ticket detail page
        const detailStatus = document.getElementById('ticket-status');
        if (detailStatus) {
            detailStatus.textContent = newStatus;
        }
    },

    /**
     * Update ticket priority badge
     * @param {string} ticketId - Ticket ID
     * @param {string} newPriority - New priority value
     */
    updatePriority(ticketId, newPriority) {
        const ticketCard = document.querySelector(`[data-ticket-id="${ticketId}"]`);
        if (ticketCard) {
            const priorityBadge = ticketCard.querySelector('.ticket-priority, .priority-badge, [data-priority]');
            if (priorityBadge) {
                priorityBadge.textContent = newPriority;
                priorityBadge.className = priorityBadge.className.replace(/priority-\w+/g, '');
                priorityBadge.classList.add(`priority-${newPriority.toLowerCase()}`);
            }

            // Update border indicator
            ticketCard.classList.remove('border-red-500', 'border-orange-500', 'border-yellow-500', 'border-green-500');
            const borderColors = {
                'Urgent': 'border-red-500',
                'High': 'border-orange-500',
                'Medium': 'border-yellow-500',
                'Low': 'border-green-500'
            };
            if (borderColors[newPriority]) {
                ticketCard.classList.add(borderColors[newPriority]);
            }
        }
    },

    /**
     * Update technician assignment display
     * @param {string} ticketId - Ticket ID  
     * @param {string} technicianName - Technician name
     */
    updateTechnician(ticketId, technicianName) {
        const ticketCard = document.querySelector(`[data-ticket-id="${ticketId}"]`);
        if (ticketCard) {
            const techBadge = ticketCard.querySelector('.assigned-technician, [data-technician]');
            if (techBadge) {
                techBadge.textContent = technicianName;
            }
        }
    },

    /**
     * Remove ticket from list (for forwarding/reassignment)
     * @param {string} ticketId - Ticket ID
     * @param {boolean} animate - Whether to animate removal
     */
    removeTicket(ticketId, animate = true) {
        const ticketCard = document.querySelector(`[data-ticket-id="${ticketId}"]`);
        if (!ticketCard) return;

        if (animate) {
            ticketCard.style.transition = 'all 0.3s ease';
            ticketCard.style.opacity = '0';
            ticketCard.style.transform = 'translateX(100px)';
            setTimeout(() => ticketCard.remove(), 300);
        } else {
            ticketCard.remove();
        }

        // Update ticket count if visible
        this.updateTicketCount(-1);
    },

    /**
     * Add a new ticket to the list
     * @param {object} ticketData - Ticket data
     * @param {string} containerId - Container element ID
     * @param {function} renderFn - Optional custom render function
     */
    addTicket(ticketData, containerId = 'ticket-list', renderFn = null) {
        const container = document.getElementById(containerId) || document.querySelector('.ticket-list');
        if (!container) return;

        // Use custom render or default
        const html = renderFn ? renderFn(ticketData) : this._defaultTicketHtml(ticketData);

        // Insert at beginning
        container.insertAdjacentHTML('afterbegin', html);

        // Animate in
        const newCard = container.firstElementChild;
        if (newCard) {
            newCard.style.opacity = '0';
            newCard.style.transform = 'translateY(-20px)';
            requestAnimationFrame(() => {
                newCard.style.transition = 'all 0.3s ease';
                newCard.style.opacity = '1';
                newCard.style.transform = 'translateY(0)';
            });
        }

        this.updateTicketCount(1);
    },

    /**
     * Update ticket count displays
     * @param {number} delta - Change in count (+1 or -1)
     */
    updateTicketCount(delta) {
        const countElements = document.querySelectorAll('.ticket-count, [data-ticket-count]');
        countElements.forEach(el => {
            const current = parseInt(el.textContent) || 0;
            el.textContent = Math.max(0, current + delta);
        });
    },

    /**
     * Toggle bookmark/importance indicator
     * @param {string} ticketId - Ticket ID
     * @param {boolean} isImportant - Whether marked as important
     */
    updateBookmark(ticketId, isImportant) {
        const ticketCard = document.querySelector(`[data-ticket-id="${ticketId}"]`);
        if (ticketCard) {
            const bookmarkIcon = ticketCard.querySelector('.bookmark-icon, [data-bookmark]');
            if (bookmarkIcon) {
                if (isImportant) {
                    bookmarkIcon.classList.add('text-yellow-500', 'fas');
                    bookmarkIcon.classList.remove('text-gray-400', 'far');
                } else {
                    bookmarkIcon.classList.remove('text-yellow-500', 'fas');
                    bookmarkIcon.classList.add('text-gray-400', 'far');
                }
            }
        }
    },

    /**
     * Show toast notification
     * @param {string} message - Message to show
     * @param {string} type - 'success', 'error', 'info', 'warning'
     */
    showToast(message, type = 'info') {
        // Create toast container if not exists
        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            container.style.cssText = 'position: fixed; top: 80px; right: 20px; z-index: 10000; display: flex; flex-direction: column; gap: 10px;';
            document.body.appendChild(container);
        }

        const colors = {
            success: '#10B981',
            error: '#EF4444',
            warning: '#F59E0B',
            info: '#3B82F6'
        };

        const toast = document.createElement('div');
        toast.style.cssText = `
            background: rgba(20, 20, 30, 0.95);
            backdrop-filter: blur(20px);
            border: 1px solid ${colors[type] || colors.info};
            border-left: 4px solid ${colors[type] || colors.info};
            color: white;
            padding: 16px 20px;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
            max-width: 350px;
            animation: slideInToast 0.3s ease;
        `;
        toast.innerHTML = `
            <div style="display: flex; align-items: center; gap: 12px;">
                <i class="fas ${type === 'success' ? 'fa-check-circle' : type === 'error' ? 'fa-exclamation-circle' : type === 'warning' ? 'fa-exclamation-triangle' : 'fa-info-circle'}" style="color: ${colors[type] || colors.info};"></i>
                <span>${message}</span>
            </div>
        `;

        // Add animation styles
        if (!document.getElementById('toast-styles')) {
            const styles = document.createElement('style');
            styles.id = 'toast-styles';
            styles.textContent = `
                @keyframes slideInToast {
                    from { opacity: 0; transform: translateX(100px); }
                    to { opacity: 1; transform: translateX(0); }
                }
                @keyframes slideOutToast {
                    from { opacity: 1; transform: translateX(0); }
                    to { opacity: 0; transform: translateX(100px); }
                }
            `;
            document.head.appendChild(styles);
        }

        container.appendChild(toast);

        // Auto remove after 5 seconds
        setTimeout(() => {
            toast.style.animation = 'slideOutToast 0.3s ease forwards';
            setTimeout(() => toast.remove(), 300);
        }, 5000);
    },

    /**
     * Default ticket card HTML (customize per page)
     * @private
     */
    _defaultTicketHtml(ticket) {
        return `
            <div class="ticket-card glass-card" data-ticket-id="${ticket.ticket_id || ticket._id}">
                <div class="flex items-center gap-3">
                    <span class="ticket-id">#${ticket.ticket_id || ticket._id}</span>
                    <span class="priority-badge priority-${(ticket.priority || 'medium').toLowerCase()}">${ticket.priority || 'Medium'}</span>
                </div>
                <h3 class="ticket-subject">${ticket.subject || 'No Subject'}</h3>
                <p class="ticket-preview">${ticket.name || 'Unknown'}</p>
            </div>
        `;
    }
};


// Export for use in other scripts
if (typeof window !== 'undefined') {
    window.SocketManager = SocketManager;
    window.TicketUIUpdater = TicketUIUpdater;
}
