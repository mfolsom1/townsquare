import React from 'react';
import { Link } from 'react-router-dom';
import PropTypes from 'prop-types';
import './EventCard.css'; // optional, reuse existing styles

function EventCard({ event, isSaved, onToggleSaved }) {
  const [clicked, setClicked] = React.useState(false);
  const [leaving, setLeaving] = React.useState(false);
  const [removedTag, setRemovedTag] = React.useState(false);

  const handleHeart = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (isSaved(event.event_id)) {
      setClicked(true);
      setRemovedTag(true);
      setLeaving(true);
      const region = document.getElementById('sr-announce');
      if (region) region.textContent = `Removed ${event.title} from Saved`;
      setTimeout(() => onToggleSaved(event), 220);
      setTimeout(() => setRemovedTag(false), 900);
    } else {
      setClicked(true);
      onToggleSaved(event);
      setTimeout(() => setClicked(false), 200);
    }
  };

  const imageUrl = event.image_url || 'https://placehold.co/600x400/EEE/31343C?text=Townsquare';

  return (
    <Link to={`/events/${event.event_id}`} className={`event-card ${leaving ? 'leaving' : ''}`}>
      <div className="event-card-image-wrapper">
        <img src={imageUrl} alt={event.title} className="event-card-image" />
        <button
          className={`event-save ${isSaved(event.event_id) ? 'saved' : ''} ${clicked ? 'pulse' : ''}`}
          aria-pressed={isSaved(event.event_id)}
          aria-label={isSaved(event.event_id) ? 'Unsave event' : 'Save event'}
          onClick={handleHeart}
        >
          <span className="material-symbols-outlined event-heart">favorite</span>
        </button>

        {removedTag && <span className="event-removed-chip" aria-hidden="true">Removed</span>}
      </div>

      <div className="event-card-body">
        <h3 className="event-card-title">{event.title}</h3>
        <p className="event-card-time">{new Date(event.start_time).toLocaleString()}</p>
        <p className="event-card-location">{event.location}</p>
        <p className="event-card-description">
          {event.description?.length > 100 ? `${event.description.slice(0, 100)}…` : event.description}
        </p>
      </div>
    </Link>
  );
}

EventCard.propTypes = {
  event: PropTypes.object.isRequired,
  isSaved: PropTypes.func.isRequired,
  onToggleSaved: PropTypes.func.isRequired
};

export default React.memo(EventCard);
