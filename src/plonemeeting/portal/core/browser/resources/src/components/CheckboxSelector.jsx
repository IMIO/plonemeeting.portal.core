import {useState} from "preact/hooks";

const CheckboxSelector = ({scope, checked}) => {
  const [selected, setSelected] = useState(checked);

  const handleClick = () => {
    const checkboxes = document
      .getElementById(scope)
      .querySelectorAll('input[type="checkbox"]')
    for (let checkbox of checkboxes){
      checkbox.checked = !selected
    }
    setSelected(!selected)
  }

  return <input type="checkbox" onClick={handleClick} checked={selected} title="Tout cocher/décocher" />
}

export default CheckboxSelector;
