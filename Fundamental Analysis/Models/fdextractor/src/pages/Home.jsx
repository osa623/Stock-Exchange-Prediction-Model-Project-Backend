import React from 'react';
import { useNavigate } from 'react-router-dom';

const Home = () => {

    const navigate = useNavigate();

    return (
        <div className="container mx-auto p-8">
            <section className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="p-6 border h-screen rounded-lg shadow-sm">
                    <h2 className="text-xl mb-2 font-bold">User Management</h2>
                    <p className="text-gray-600">Manage Users and their roles</p>
                    <div className='w-full h-1 mt-2 bg-gray-200 rounded-full'>
                        <div className='h-1 bg-gray-900 w-1/2 rounded-full'></div>
                    </div>
                    <div className='flex rounded-3xl mt-2 w-full h-[65%] bg-black'
                        style={{
                            boxShadow: 'inset 0px 10px 10px rgba(255,255,255,0.5)'
                        }}>

                    </div>
                </div>
                <div className="p-6 border h-screen rounded-lg shadow-sm">
                    <h2 className="text-xl mb-2 font-bold">DataBase Handling</h2>
                    <p className="text-gray-600">Manage Users and their roles</p>
                    <div className='w-full h-1 mt-2 bg-gray-200 rounded-full'>
                        <div className='h-1 bg-gray-900 w-1/2 rounded-full'></div>
                    </div>
                    <div className='flex rounded-3xl mt-2 w-full h-[65%] bg-black'
                        style={{
                            boxShadow: 'inset 0px 10px 10px rgba(255,255,255,0.5)'
                        }}>

                    </div>
                </div>
                <div className="p-6 border h-screen rounded-lg shadow-sm">
                    <h2 className="text-xl mb-2 font-bold">PDF Extractor</h2>
                    <p className="text-gray-600">Manage Users and their roles</p>
                    <div className='w-full h-1 mt-2 bg-gray-200 rounded-full'>
                        <div className='h-1 bg-gray-900 w-1/2 rounded-full'></div>
                    </div>
                    <div onClick={() => navigate('/dashboard')} className='flex cursor-pointer rounded-3xl mt-2 w-full h-[65%] bg-black'
                        style={{
                            boxShadow: 'inset 0px 10px 10px rgba(255,255,255,0.5)'
                        }}>

                    </div>
                </div>
            </section>
        </div>
    );
};

export default Home;
