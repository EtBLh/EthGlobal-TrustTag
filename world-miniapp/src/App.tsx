import { HashRouter, Route, Routes, useLocation } from "react-router";
import SplashScreen from "./page";
import HomePage from "./page/home";
import VotePage from "./page/vote";
import ProposePage from "./page/propose";
import SearchPage from "./page/search";
import PageWrapper from "./components/page-wrapper";
import { AnimatePresence } from "framer-motion";
import ClaimPage from "./page/claim";

export function AnimatedRoutes() {
  const location = useLocation()
  return (
      <AnimatePresence mode="wait">
        <Routes location={location} key={location.pathname}>
          <Route index element={<SplashScreen />} />
          <Route path='/home' element={<PageWrapper variant="ltr"><HomePage /></PageWrapper>} />
          <Route path='/vote' element={<PageWrapper variant="ltr"><VotePage /></PageWrapper>} />
          <Route path='/search' element={<PageWrapper variant="ltr"><SearchPage /></PageWrapper>} />
          <Route path='/propose' element={<PageWrapper variant="ltr"><ProposePage /></PageWrapper>} />
          <Route path='/claim' element={<PageWrapper variant="ltr"><ClaimPage /></PageWrapper>} />
        </Routes>
      </AnimatePresence>
  )
}

export default function () {
  return <HashRouter>
      <AnimatedRoutes/>
  </HashRouter>
}