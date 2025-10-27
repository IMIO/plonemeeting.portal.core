import React, { useEffect, useState } from "react";

const TableOfContent = () => {
  const [items, setItems] = useState([]);

  useEffect(() => {
    // Build the list of TOC items once
    const elements = Array.from(document.querySelectorAll("[data-toc]")).map(
      (el) => ({
        id: el.id || el.getAttribute("data-toc"),
        label: el.getAttribute("data-toc"),
        offsetTop: el.offsetTop,
      })
    );

    setItems(elements);
  }, []);

  const handleScrollTo = (id) => {
    const target = document.getElementById(id);
    if (target) {
      window.scrollTo({
        top: target.offsetTop - 250, // adjust for fixed headers
        behavior: "smooth",
      });
    }
  };

  return (
    <div
      className="position-fixed top-50 end-0 translate-middle-y bg-dark shadow-md text-white p-3 rounded"
      style={{
        width: "250px",
        zIndex: 1050,
        maxHeight: "70vh",
        overflowY: "auto",
      }}
    >
      <h5 className="mb-3 border-bottom pb-2">Table of Contents</h5>
      <ul className="list-unstyled mb-0">
        {items.map((item) => (
          <li key={item.id} className="mb-2">
            <a
              href={`#${item.id}`}
              className="text-decoration-none d-block px-2 py-1 rounded hover-shadow"
              onClick={(e) => {
                e.preventDefault();
                handleScrollTo(item.id);
              }}
            >
              {item.label}
            </a>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default TableOfContent;
