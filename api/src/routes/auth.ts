import { Router } from 'express';
import { AuthController } from '../controllers/AuthController';
import { authMiddleware } from '../middleware/auth';

const router = Router();

router.post('/signup', AuthController.signup);

router.post('/login', AuthController.login);

router.get('/profile', authMiddleware, AuthController.getProfile);

export default router;
