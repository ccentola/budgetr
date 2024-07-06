import { useEffect, useState } from "react";
import axios from "axios";
import { usePlaidLink } from "react-plaid-link";
// import './App.css'

axios.defaults.baseURL = "http://localhost:8000";

function PlaidAuth({ publicToken }) {
  const [account, setAccount] = useState();
  const [transactions, setTransactions] = useState();
  const [balance, setBalance] = useState();
  const [items, setItems] = useState();
  const [accounts, setAccounts] = useState();

  useEffect(() => {
    async function fetchData() {
      let accessToken = await axios.post("/api/set_access_token", {
        public_token: publicToken,
      });
      console.log("accessToken", accessToken.data);
      const auth = await axios.post("/api/auth", {
        access_token: accessToken.data.accessToken,
      });
      console.log("auth data ", auth.data);
      setAccount(auth.data.numbers.ach[0]);
      const transactions = await axios.post("/api/transactions", {
        access_token: accessToken.data.accessToken,
      });
      console.log("transaction data ", transactions.data);
      setTransactions(transactions.data);
      const balance = await axios.post("/api/balance", {
        access_token: accessToken.data.accessToken,
      });
      console.log("balance data ", balance.data);
      setBalance(balance.data);
      const accounts = await axios.post("/api/accounts", {
        access_token: accessToken.data.accessToken,
      });
      console.log("accounts data ", accounts.data);
      setAccounts(accounts.data);
    }
    fetchData();
  }, []);
  return (
    transactions && (
      <>
        <p>Account number: {account.account}</p>
        <p>Routing number: {account.routing}</p>
      </>
    )
  );
}

function App() {
  const [linkToken, setLinkToken] = useState();
  const [publicToken, setPublicToken] = useState();

  useEffect(() => {
    async function fetch() {
      const response = await axios.post("/api/create_link_token");
      setLinkToken(response.data.link_token);
    }
    fetch();
  }, []);

  const { open, ready } = usePlaidLink({
    token: linkToken,
    onSuccess: (public_token, metadata) => {
      setPublicToken(public_token);
      console.log("success", public_token, metadata);
      // send public_token to server
    },
  });

  return publicToken ? (
    <PlaidAuth publicToken={publicToken} />
  ) : (
    <button onClick={() => open()} disabled={!ready}>
      Connect a bank account
    </button>
  );
}

export default App;
