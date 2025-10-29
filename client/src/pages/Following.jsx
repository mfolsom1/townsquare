import React from 'react';
import './Following.css'

export default function Following() {
  return (
    <main className='main-container'>
      <div>
        <h1 className='page-header'>Following</h1>
        <p className='page-subheading'>Events from people and organizations you follow</p>
      </div>
      
      {/* Friends Section */}
      <div>
        <h2 className='friends-header'>Events with People You Follow</h2>
        <div>
          Cards
        </div>
      </div>

      {/* Organizations Section */}
      <div>
        <h2 className='orgs-header'>Events from Organizations You Follow</h2>
        <div>
          Cards
        </div>
      </div>
    </main>
  )
}
