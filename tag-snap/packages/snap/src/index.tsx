import type { OnTransactionHandler } from '@metamask/snaps-sdk';
import { Box, Text, Bold } from '@metamask/snaps-sdk/jsx';

export const onTransaction: OnTransactionHandler = async ({transaction, chainId}) => {
  const { from, to, value } = transaction;

  return {
    content: (
    <Box>
      <Text>
        <Bold>Transaction Details:</Bold>
      </Text>
      <Text>From: {from}</Text>
      <Text>To: {to}</Text>
      <Text>Value: {value}</Text>
    </Box>
  )};
}
