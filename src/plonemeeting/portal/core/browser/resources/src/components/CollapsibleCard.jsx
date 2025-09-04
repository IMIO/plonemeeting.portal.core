import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { BsChevronUp } from "react-icons/bs";
import { BsChevronDown } from "react-icons/bs";

const CollapsibleCard = ({ id, title, content }) => {
  // Initialize open/closed from localStorage
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    const saved = localStorage.getItem(`collapsible-${id}`);
    if (saved !== null) {
      setIsOpen(saved === 'true');
    }
  }, [id]);

  const toggle = () => {
    const next = !isOpen;
    setIsOpen(next);
    localStorage.setItem(`collapsible-${id}`, next);
  };

  return (
    <div className="card card-outline mb-3">
      <div className="card-header d-flex align-items-center">
        <h2 className="h2 mb-0">{title}</h2>
        <button
          className="btn btn-secondary btn-sm"
          onClick={toggle}
          aria-expanded={isOpen}
          aria-controls={`collapse-${id}`}
        >
            {isOpen ? <BsChevronUp /> : <BsChevronDown />}
            <span className="visually-hidden">{isOpen ? 'Réduire' : 'Développer'}</span>
        </button>
      </div>

      <AnimatePresence initial={false}>
        {isOpen && (
          <motion.div
            id={`collapse-${id}`}
            className="card-body"
            style={{padding: "0rem !important"}}
            initial="collapsed"
            animate="open"
            exit="collapsed"
            variants={{
              open: { height: 'auto', opacity: 1, padding: 0 },
              collapsed: { height: 0, opacity: 0, padding: 0 }
            }}
            transition={{ duration: 0.22, ease: 'easeInOut' }}
          >
            {content}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default CollapsibleCard;
