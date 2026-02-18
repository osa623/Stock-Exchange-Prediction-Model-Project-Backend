const ExtractedData = require('../models/reportData');


// 2. Get Folder Structure (Hierarchy for Frontend)
exports.getDataStructure = async (req, res) => {
    try {
        // Aggregate unique Sectors -> Companies -> Years
        const structure = await ExtractedData.aggregate([
            {
                $group: {
                    _id: {
                        sector: "$sector",
                        company: "$company",
                        year: "$year"
                    },
                    types: { $push: { type: "$type", id: "$_id" } }
                }
            },
            {
                $group: {
                    _id: { sector: "$_id.sector", company: "$_id.company" },
                    years: {
                        $push: {
                            year: "$_id.year",
                            files: "$types"
                        }
                    }
                }
            },
            {
                $group: {
                    _id: "$_id.sector",
                    companies: {
                        $push: {
                            company: "$_id.company",
                            years: "$years"
                        }
                    }
                }
            },
            { $sort: { _id: 1 } } // Sort by Sector
        ]);

        console.log("Aggregation Result:", JSON.stringify(structure, null, 2));
        res.json(structure);
    } catch (error) {
        console.error("Get Structure Error:", error);
        res.status(500).json({ error: "Failed to fetch structure" });
    }
};

// 3. Get Single Record by ID
exports.getDataById = async (req, res) => {
    try {
        const { id } = req.params;
        const record = await ExtractedData.findById(id);

        if (!record) {
            return res.status(404).json({ error: "Record not found" });
        }

        res.json(record);
    } catch (error) {
        console.error("Get Data Error:", error);
        res.status(500).json({ error: "Failed to fetch data" });
    }
};


