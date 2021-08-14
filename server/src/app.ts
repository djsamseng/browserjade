import express, { Express } from "express";
import cors from "cors";
import routes from "./routes/index";
import { Server as SocketIOServer } from "socket.io";

const app = express();
const PORT = process.env.PORT || 4000;

app.use(cors());
app.use(routes);

const server = app.listen(PORT, () => {
    console.log("Server running on port:", PORT);
});

const io = new SocketIOServer(server);

io.on("connection", (socket) => {
    console.log("Got socket.io connection");
    socket.on("offer", (offer) => {
        socket.broadcast.emit("offer", offer);
    });
    socket.on("answer", (answer) => {
        socket.broadcast.emit("answer", answer);
    });
    socket.on("candidate", (candidate) => {
        socket.broadcast.emit("candidate", candidate);
    });
    socket.on("ready", () => {
        socket.broadcast.emit("ready");
    });
    socket.on("create or join", (room) => {
        console.log('create or join');
        const roomSockets = io.sockets.adapter.rooms.get(room);
        if (!roomSockets) {
            socket.join(room);
            console.log("Created room:", room);
            socket.emit('created', room, socket.id);
            return;
        }
        const numClientsInRoom = roomSockets.size;
        if (numClientsInRoom === 0) {
            socket.join(room);
            console.log("Created room:", room);
            socket.emit('created', room, socket.id);
        }
        else {
            io.sockets.in(room).emit('join', room);
            console.log("Room:", room, " now has ", numClientsInRoom + 1, " client(s)");
            socket.join(room);
            socket.emit('joined', room, socket.id);
        }
    });
    socket.on('disconnecting', () => {
        console.log("disconnecting:", socket.id);
        const roomsWasIn = io.sockets.adapter.sids.get(socket.id);
        if (!roomsWasIn) {
            console.log("Disconnecting: was not in any rooms");
            return;
        }
        for (const roomName of roomsWasIn.keys()) {
            const room = io.sockets.adapter.rooms.get(roomName);
            if (room) {
                const numRemainingClients = room.size - 1;
                console.log("Disconnecting: was in room:", roomName);
                console.log("Room:", roomName, " now has ", numRemainingClients, " client(s)");
                if (numRemainingClients === 1) {
                    console.log("Sending isInitiator");
                    io.sockets.in(roomName).emit("isinitiator", roomName);
                }
            }

        }
    })
});
