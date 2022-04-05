import React, { useEffect, useCallback } from 'react';
import { useHistory } from 'react-router-dom';

import GoogleButton from 'react-google-button';
import { FaFacebookF } from 'react-icons/fa';

import { notifyError } from 'utils/notifications';
import { GithubStars, Layout } from 'components';

import styles from './Login.module.css';

const { REACT_APP_GOOGLE_CLIENT_ID, REACT_APP_FACEBOOK_CLIENT_ID, REACT_APP_BASE_BACKEND_URL, REACT_APP_SECRET_FACEBOOK_STATE } = process.env;

const Login = () => {
  const history = useHistory();

  useEffect(() => {
    const queryParams = new URLSearchParams(history.location.search);

    const error = queryParams.get('error');

    if (error) {
      notifyError(error);
      history.replace({ search: null });
    }
  }, [history]);

  const openGoogleLoginPage = useCallback(() => {
    const googleAuthUrl = 'https://accounts.google.com/o/oauth2/v2/auth';
    const redirectUri = 'api/v1/users/auth/login/google/';

    const scope = [
      'https://www.googleapis.com/auth/userinfo.email',
      'https://www.googleapis.com/auth/userinfo.profile'
    ].join(' ');

    const params = {
      response_type: 'code',
      client_id: REACT_APP_GOOGLE_CLIENT_ID,
      redirect_uri: `${REACT_APP_BASE_BACKEND_URL}/${redirectUri}`,
      prompt: 'select_account',
      access_type: 'offline',
      scope
    };

    const urlParams = new URLSearchParams(params).toString();

    window.location = `${googleAuthUrl}?${urlParams}`;
  }, []);
  
  const openFacebookLoginPage = useCallback(() => {
    const facebookAuthUrl = 'https://www.facebook.com/v13.0/dialog/oauth';
    const redirectUri = 'api/v1/users/auth/login/facebook/';

    const params = {
      client_id: REACT_APP_FACEBOOK_CLIENT_ID,
      redirect_uri: `${REACT_APP_BASE_BACKEND_URL}/${redirectUri}`,
      state: REACT_APP_SECRET_FACEBOOK_STATE,
      auth_type: 'rerequest',
      fields: "name,email,picture",
      scope: 'email',
      // scope: "public_profile,user_friends,user_actions.books",
    };

    const urlParams = new URLSearchParams(params).toString();

    window.location = `${facebookAuthUrl}?${urlParams}`;
  }, []);

  return (
    <Layout className={styles.content}>
      <h1 className={styles.pageHeader}>Welcome to our Demo App!</h1>

      <h2 className={styles.btnHeader}>Sign In with Google:</h2>
      <GoogleButton
        onClick={openGoogleLoginPage}
        label="Sign in with Google"
        disabled={!REACT_APP_GOOGLE_CLIENT_ID}
      />

      <h2 className={styles.btnHeader}>Sign In with Facebook:</h2>

      {/* <FacebookLogin
        appId="1088597931155576"
        autoLoad={true}
        fields="name,email,picture"
        callback={responseFacebook}
        link="https://api.facebook.com"
        // cssClass="my-facebook-button-class"
        size='medium'
        icon="fa-facebook"
      /> */}

      <button 
        className={styles.btnFacebook} 
        onClick={openFacebookLoginPage}
        disabled={!REACT_APP_FACEBOOK_CLIENT_ID}
        >
        <FaFacebookF />
        Login with Facebook
      </button>

      <GithubStars className={styles.githubStars} />
    </Layout>
  );
};

export default Login;
