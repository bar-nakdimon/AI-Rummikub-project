import { Router } from 'express';
import multer, { FileFilterCallback } from 'multer';
import { VisionController } from '../controllers/visionController';
import { authMiddleware } from '../middleware/auth';

const router = Router();

/**
 * Configure multer for handling file uploads
 * - Limits: 10MB per file, 20MB total
 * - Accepts any image/* MIME type
 */
const upload = multer({
  storage: multer.memoryStorage(),
  limits: {
    fileSize: 10 * 1024 * 1024, // 10MB per file
  },
  fileFilter: (req: any, file: any, cb: FileFilterCallback): void => {
    if (typeof file.mimetype === 'string' && file.mimetype.startsWith('image/')) {
      cb(null, true);
    } else {
      cb(new Error('Only image uploads are allowed') as any, false);
    }
  },
});

router.post(
  '/analyze',
  authMiddleware as any,
  upload.fields([
    { name: 'myBoard', maxCount: 1 },
    { name: 'sharedBoard', maxCount: 1 },
  ]),
  VisionController.analyzeBoards as any
);

router.post(
  '/feedback',
  authMiddleware as any,
  upload.fields([
    { name: 'rackImage', maxCount: 1 },
    { name: 'boardImage', maxCount: 1 },
  ]),
  VisionController.submitFeedback as any
);

router.get('/health', authMiddleware as any, VisionController.healthCheck as any);

export default router;
