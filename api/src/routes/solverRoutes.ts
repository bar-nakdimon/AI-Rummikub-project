import { Router } from 'express';
import { SolverController } from '../controllers/solverController';
import { authMiddleware } from '../middleware/auth';

const router = Router();

router.post('/solve', authMiddleware as any, SolverController.solve);

router.post('/validate', authMiddleware as any, SolverController.validate);

export default router;
