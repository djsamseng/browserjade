import { Router } from "express";

const router = Router();

router.get("/letters", (req, resp) => {
    const x = req.query.x;
    const y = req.query.y;
    const size = req.query.size || 24;
    const rotate = req.query.rotate || 0;
    resp.send(`
    <html>
        <body>
            <div 
                style="
                    position:absolute;left:${x};top:${y};
                    font-size:${size};
                    transform:rotate(${rotate}deg);
                ">
                ${req.query.letter}
            </div>
        <body>
    </html>`);
});

export default router;