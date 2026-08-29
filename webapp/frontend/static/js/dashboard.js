// Minimal JavaScript for dashboard interactions
document.addEventListener('DOMContentLoaded', function() {
    // Logout functionality
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', async function() {
            try {
                const response = await fetch('/logout', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });
                const data = await response.json();
                if (data.success) {
                    window.location.href = '/login';
                }
            } catch (error) {
                console.error('Logout error:', error);
                window.location.href = '/login';
            }
        });
    }
    
    // Manual priority override buttons
    document.querySelectorAll('.priority-override-btn').forEach(btn => {
        btn.addEventListener('click', async function() {
            const commitmentId = this.dataset.id;
            const newPriority = this.dataset.priority;
            
            try {
                const response = await fetch(`/api/commitments/${commitmentId}/priority`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ priority: newPriority })
                });
                
                if (response.ok) {
                    location.reload();
                } else {
                    alert('Failed to update priority');
                }
            } catch (error) {
                console.error('Priority update error:', error);
                alert('An error occurred');
            }
        });
    });
    
    // Status update buttons
    document.querySelectorAll('.status-btn').forEach(btn => {
        btn.addEventListener('click', async function() {
            const commitmentId = this.dataset.id;
            const newStatus = this.dataset.status;
            
            try {
                const response = await fetch(`/api/commitments/${commitmentId}/status`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ status: newStatus })
                });
                
                if (response.ok) {
                    location.reload();
                } else {
                    alert('Failed to update status');
                }
            } catch (error) {
                console.error('Status update error:', error);
                alert('An error occurred');
            }
        });
    });
    
    // Delete buttons
    document.querySelectorAll('.delete-btn').forEach(btn => {
        btn.addEventListener('click', async function() {
            if (!confirm('Are you sure you want to delete this commitment?')) {
                return;
            }
            
            const commitmentId = this.dataset.id;
            
            try {
                const response = await fetch(`/api/commitments/${commitmentId}`, {
                    method: 'DELETE'
                });
                
                if (response.ok) {
                    location.reload();
                } else {
                    alert('Failed to delete commitment');
                }
            } catch (error) {
                console.error('Delete error:', error);
                alert('An error occurred');
            }
        });
    });
    
    // Close urgent modal
    window.closeUrgentModal = function() {
        document.getElementById('urgentModal').classList.remove('show');
    };
});
