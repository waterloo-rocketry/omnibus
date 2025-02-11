import { useEffect, useState } from 'react';
import './App.css'
import D3LineChart from './components/D3LineChart/D3LineChart';

function App() {

  let [data, updateData] = useState<any[]>([]);

  useEffect(() => {

    const socket = new WebSocket("ws://localhost:8888/ws");

    socket.addEventListener("open", () => {
      socket.send("Connection established");
    });
    
    socket.addEventListener("message", event => {

      let parsedData = JSON.parse(event.data);
      
      updateData((prevData) => { return [...prevData, [parsedData["timestamp"], parsedData["data"]["Fake0"][0]]] })
    });

    return () => {
      socket.close();
    };
  }, [])

  return (
    <D3LineChart data={data}/>
  )
}

export default App
