import { Router } from "express";

const router = Router();

router.get("/letters", (req, resp) => {
    resp.send(req.query.letter);
});

export default router;