import React from 'react';
import { useNavigate } from 'react-router-dom';

const FeatureCard = ({ title, description, onClick }) => (
    <div
        onClick={onClick}
        className={`group p-8 border border-gray-100 rounded-3xl shadow-sm transition-all duration-500 hover:shadow-xl hover:-translate-y-2 bg-white ${onClick ? 'cursor-pointer' : ''}`}
    >
        <div className="mb-6">
            <h2 className="text-2xl font-bold text-gray-900 tracking-tight">{title}</h2>
            <p className="text-gray-500 mt-1 font-medium">{description}</p>
        </div>

        <div className='w-full h-1.5 bg-gray-100 rounded-full overflow-hidden'>
            <div className='h-full bg-black w-1/3 rounded-full transition-all duration-700 group-hover:w-1/2'></div>
        </div>

        <div className='relative mt-8 w-full h-80 bg-zinc-950 rounded-[2rem] overflow-hidden transition-transform duration-500 group-hover:scale-[1.02]'
            style={{
                boxShadow: 'inset 0px 20px 40px rgba(255,255,255,0.1), inset 0px -10px 20px rgba(0,0,0,0.4)'
            }}>
            <div className="absolute inset-0 bg-gradient-to-tr from-transparent via-white/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-700" />
        </div>
    </div>
);

const Home = () => {
    const navigate = useNavigate();

    const features = [
        {
            title: "User Management",
            description: "Manage Users and their roles",
            action: null
        },
        {
            title: "DataBase Handling",
            description: "Manage system data structures",
            action: null
        },
        {
            title: "PDF Extractor",
            description: "Automated document data extraction",
            action: () => navigate('/dashboard')
        }
    ];

    return (
        <div className="min-h-screen bg-gray-50/50 flex items-center justify-center p-6">
            <div className="max-w-7xl w-full mx-auto">
                <section className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    {features.map((feature, idx) => (
                        <FeatureCard
                            key={idx}
                            title={feature.title}
                            description={feature.description}
                            onClick={feature.action}
                        />
                    ))}
                </section>
            </div>
        </div>
    );
};

export default Home;
