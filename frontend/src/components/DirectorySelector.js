"use client"
import { useState } from 'react';

export default function DirectorySelector() {
  const [path, setPath] = useState("");
  const [status, setStatus] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    const res = await fetch('/api/set-directory', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ path }),
    });
    const data = await res.json();
    setStatus(data.message || data.detail);
  };

  return (
    <div className="p-4 bg-gray-100 rounded-xl shadow">
      <form onSubmit={handleSubmit}>
        <label className="block font-semibold mb-2">Directory to Monitor:</label>
        <input 
          type="text"
          value={path}
          onChange={(e) => setPath(e.target.value)}
          className="border px-2 py-1 rounded w-full mb-2"
          placeholder="/mnt/data or /home/user/folder"
        />
        <button className="bg-blue-600 text-white px-4 py-1 rounded hover:bg-blue-700">
          Set Directory
        </button>
      </form>
      <p className="mt-2 text-sm">{status}</p>
    </div>
  );
}
