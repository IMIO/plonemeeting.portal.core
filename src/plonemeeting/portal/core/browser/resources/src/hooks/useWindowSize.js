import {useState, useLayoutEffect} from "preact/hooks";

const useWindowSize = () => {
  const [size, setSize] = useState({
    width: window.innerWidth,
    height: window.innerHeight
  })

  useLayoutEffect(() => {
    const updateSize = () => {
      setSize({
        width: window.innerWidth, height: window.innerHeight
      })
    }

    window.addEventListener('resize', updateSize)

    updateSize()

    return () => window.removeEventListener('resize', updateSize)
  }, [])

  return size
}
export default useWindowSize;
