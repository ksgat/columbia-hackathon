import { PrivyProvider } from '@privy-io/react-auth'

export const privyConfig = {
  appId: process.env.NEXT_PUBLIC_PRIVY_APP_ID || '',
  config: {
    loginMethods: ['google', 'email'],
    appearance: {
      theme: 'dark',
      accentColor: '#8B5CF6',
    },
    embeddedWallets: {
      createOnLogin: 'users-without-wallets',
    },
  },
}
