const express = require('express');
const router = express.Router();
const {
    getDataStructure,
    getDataById,

} = require('../controllers/reportController');


// Get hierarchical structure (Sector -> Company -> Year)
router.get('/structure', getDataStructure);

// Get specific record
router.get('/:id', getDataById);


module.exports = router;
