import express, { Express } from "express";
import bodyParser from "body-parser";
import cors from "cors";
import routes from "./routes/index";
import { Server as SocketIOServer } from "socket.io";
import Puppeteer, { Browser, Page, CDPSession } from "puppeteer";
import { installMouseHelper } from "./install-mouse-helper";
import fs from "fs";

const app = express();
const PORT = process.env.PORT || 4000;
const jsonParser = bodyParser.json();

app.use(cors());
app.use(routes);

const server = app.listen(PORT, () => {
    console.log("Server running on port:", PORT);
});

const io = new SocketIOServer(server);

class WebBrowserProxy {
    private d_browser?: Browser;
    private d_browserPage?: Page;
    private d_cdpSession?: CDPSession;
    constructor() {

    }
    public async start(socket: any) {
        if (this.d_browser) {
            await this.stop();
            await this.d_browserPage?.close();
            await this.d_browser.close();
            this.d_browser = undefined;
        }
        this.d_browser = await Puppeteer.launch({
            headless: true,
            args: [
                '--enable-usermedia-screen-capturing',
                '--allow-http-screen-capture',
                '--auto-select-desktop-capture-source=React App',

                '--use-fake-ui-for-media-stream',
                '--use-fake-device-for-media-stream',
                '--use-file-for-fake-audio-capture=/home/test.wav',
                '--allow-file-access'
            ],
            ignoreDefaultArgs: [
                '--mute-audio',
                '--hide-scrollbars'
            ]
         });
        const page = await this.d_browser.newPage();
        installMouseHelper(page);
        this.d_browserPage = page;
        page.on('console', message => console.log(message));
        const client = await page.target().createCDPSession();
        this.d_cdpSession = client;
        let cnt = 0;
        client.on('Page.screencastFrame', async (frame) => {
            console.log("Got frame:", cnt++);
            await client.send('Page.screencastFrameAck', { sessionId: frame.sessionId });
            //fs.writeFileSync('frame' + cnt + '.png', frame.data, 'base64');
            socket.emit('frame', frame.data)
        });
        await page.goto("http://google.com");
        await client.send('Page.startScreencast', {
            format: 'png', everyNthFrame: 1
        });
        console.log("Viewport:", page.viewport())
    }

    public async goto(url: string) {
        if (!this.d_browserPage) {
            throw new Error("No Browser Page");
        }
        console.log("Going to url:", url);
        await this.d_browserPage.goto(url);
        await this.d_browserPage.screenshot({ path: "test.png" });
    }

    public async mouseMove({ x, y } : { x:number, y:number }) {
        if (!this.d_browserPage) {
            throw new Error("No Browser Page");
        }
        console.log("Mouse move", { x, y});
        await this.d_browserPage.mouse.move(x, y);
    }

    public async mouseClick({ x, y } : { x: number, y:number }) {
        if (!this.d_browserPage) {
            throw new Error("No Browser Page");
        }
        console.log("Mouse click", { x, y});
        await this.d_browserPage.mouse.click(x, y);
    }

    public async scroll({ x=0, y=0 }) {
        await this.d_browserPage?.evaluate(({x,y}) => {
            window.scrollBy(x, y);
        }, {x,y});
    }

    public async stop() {
        if (!this.d_cdpSession) {
            throw new Error("No CDP Session");
        }
        await this.d_cdpSession.send('Page.stopScreencast');
    }
};

const webBrowserProxy = new WebBrowserProxy();

// routes.post("/goto", jsonParser, async (req, resp) => {
//    console.log("REQ:", req.body.url);
//    await webBrowserProxy.goto(req.body.url);
//    resp.send();
// });

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
    });
    socket.on('startWebBrowser', () => {
        webBrowserProxy.start(socket);
    });
    socket.on('goto', async (url, cb) => {
        await webBrowserProxy.goto(url);
        cb();
    });
    socket.on('mouseMove', ({ x, y }) => {
        webBrowserProxy.mouseMove({x, y});
    });
    socket.on('mouseClick', ({ x, y }) => {
        webBrowserProxy.mouseClick({ x, y});
    });
    socket.on('scroll', ({ x, y }) => {
        webBrowserProxy.scroll({ x, y });
    })
});
