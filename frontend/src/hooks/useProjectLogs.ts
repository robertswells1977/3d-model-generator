import { useState, useEffect } from 'react';
import * as signalR from '@microsoft/signalr';
import { HUB_URL } from '../api/client';

export function useProjectLogs(projectId: string | null) {
    const [logs, setLogs] = useState<string[]>([]);

    useEffect(() => {
        if (!projectId) return;

        const connection = new signalR.HubConnectionBuilder()
            .withUrl(HUB_URL)
            .withAutomaticReconnect()
            .build();

        connection.on("ReceiveLog", (message: string) => {
            setLogs(prev => [...prev, message]);
        });

        const startConnection = async () => {
            try {
                await connection.start();
                await connection.invoke("JoinProjectGroup", projectId);
            } catch (e) {
                console.error("SignalR Connection Error: ", e);
            }
        };

        startConnection();

        return () => {
            if (connection.state === signalR.HubConnectionState.Connected) {
                connection.invoke("LeaveProjectGroup", projectId)
                    .then(() => connection.stop())
                    .catch(console.error);
            } else {
                connection.stop();
            }
        };
    }, [projectId]);

    return logs;
}
