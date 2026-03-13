import { BrowserRouter, Routes, Route } from "react-router-dom"
import ChatPage from "./pages/ChatPage"
// import AdminPage from "./pages/AdminPage" // You can add this back once the file exists

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<ChatPage />} />
      </Routes>
    </BrowserRouter>
  )
}
export default App



