import './App.less';
import {HashRouter as Router, Switch, Route} from "react-router-dom";

import EntropySearchParameters from "./components/EntropySearchParameters";
import MassSearchResult from "./components/EntropySearchResult";


function App() {
    return <div className="App">
        <Router>
            <Switch>
                <Route path="/parameter" component={EntropySearchParameters}/>
                <Route path="/result" component={MassSearchResult}/>
                <Route path="/" exact component={EntropySearchParameters}/>
            </Switch>
        </Router>
    </div>

}

export default App;
