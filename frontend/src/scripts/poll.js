// https://stackoverflow.com/a/64654157
// polling functions
export async function poll (fn, fnCondition, ms) {
    let result = await fn();
    while (fnCondition(result)) {
      await wait(ms);
      result = await fn();
    }
    return result;
  };

export const pollingIntervals = Object.freeze({
  UPDATE: 5000,
  VALIDATE: 30000
})
  
const wait = function (ms = 1000) {
    return new Promise(resolve => {
        setTimeout(resolve, ms);
    });
};