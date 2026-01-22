import React, { useState } from 'react';

const LoginPage = () => {
    const [formData, setFormData] = useState({
        email: '',
        password: '',
    });

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData((prev) => ({ ...prev, [name]: value }));
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        console.log('Authenticating...', formData);
    };

    return (
        <div className="flex flex-col items-center justify-center min-h-screen bg-white text-black antialiased">
            {/* Container */}
            <div className="w-full max-w-[460px] px-8 py-12">

                {/* Header */}
                <header className="mb-10 text-center">
                    <h1 className="text-3xl font-semibold tracking-tight text-gray-900 sm:text-4xl">
                        BUYZONLABS
                    </h1>
                    <p className="mt-4 text-lg text-gray-500">
                        Admin Panel
                    </p>
                </header>

                {/* Form */}
                <form onSubmit={handleSubmit} className="space-y-4">
                    <div className="relative">
                        <input
                            type="email"
                            name="email"
                            placeholder="Email address"
                            required
                            value={formData.email}
                            onChange={handleChange}
                            className="w-full px-4 py-4 text-base bg-white border border-gray-300 rounded-xl focus:outline-none focus:ring-1 focus:ring-black focus:border-black transition-all duration-200 placeholder-gray-400"
                        />
                    </div>

                    <div className="relative">
                        <input
                            type="password"
                            name="password"
                            placeholder="Password"
                            required
                            value={formData.password}
                            onChange={handleChange}
                            className="w-full px-4 py-4 text-base bg-white border border-gray-300 rounded-xl focus:outline-none focus:ring-1 focus:ring-black focus:border-black transition-all duration-200 placeholder-gray-400"
                        />
                    </div>

                    {/* Action Button */}
                    <div className="pt-4">
                        <button
                            type="submit"
                            className="w-full py-4 text-white bg-black border border-black rounded-xl font-medium hover:bg-white hover:text-black transition-all duration-300 active:scale-[0.98]"
                        >
                            Continue
                        </button>
                    </div>
                </form>

                {/* Footer Links */}
                <footer className="mt-8 text-center space-y-4">

                </footer>
            </div>
        </div>
    );
};

export default LoginPage;