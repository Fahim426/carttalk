import React, { useState, useEffect } from 'react';

function VoiceLogs() {
    const [logs, setLogs] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchVoiceLogs();
    }, []);

    const fetchVoiceLogs = async () => {
        try {
            const res = await fetch('http://localhost:8000/api/admin/voice-logs');
            const data = await res.json();
            setLogs(data);
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    if (loading) return <div>Loading logs...</div>;

    return (
        <div style={{ background: 'white', padding: '24px', borderRadius: '16px', border: '1px solid var(--border-color)', boxShadow: 'var(--shadow-sm)' }}>
            <h4 style={{ margin: '0 0 20px', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.5px', fontSize: '14px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                🎙️ Voice Logs Activity
            </h4>

            <div style={{ overflowX: 'auto', maxHeight: '400px', overflowY: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                    <thead style={{ position: 'sticky', top: 0, background: 'white', zIndex: 1, borderBottom: '1px solid var(--border-color)' }}>
                        <tr style={{ color: '#94a3b8', fontSize: '12px' }}>
                            <th style={{ padding: '12px 16px' }}>Voice Input (Raw)</th>
                            <th style={{ padding: '12px 16px' }}>AI Interpretation</th>
                            <th style={{ padding: '12px 16px' }}>Action</th>
                            <th style={{ padding: '12px 16px' }}>Time</th>
                        </tr>
                    </thead>
                    <tbody>
                        {logs.map((log) => (
                            <tr key={log.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                                <td style={{ padding: '12px 16px', color: '#1e293b', fontStyle: 'italic' }}>
                                    "{log.voice_input}"
                                </td>
                                <td style={{ padding: '12px 16px', color: '#475569' }}>
                                    {log.ai_interpretation}
                                </td>
                                <td style={{ padding: '12px 16px' }}>
                                    <span style={{ padding: '4px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: 600, background: '#f1f5f9', color: '#475569' }}>
                                        {log.action_performed}
                                    </span>
                                </td>
                                <td style={{ padding: '12px 16px', color: '#94a3b8', fontSize: '12px' }}>
                                    {log.timestamp}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
                {logs.length === 0 && (
                    <div style={{ padding: '24px', textAlign: 'center', color: '#94a3b8', fontStyle: 'italic' }}>
                        No voice interaction logs recorded yet.
                    </div>
                )}
            </div>
        </div>
    );
}

export default VoiceLogs;
