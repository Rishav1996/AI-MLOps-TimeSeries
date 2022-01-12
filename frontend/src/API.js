export function fetchData(url, callback, data) {
  fetch(url, {
    method: "POST",
    headers: {
      mode: "no-cors",
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  })
    .then((response) => response.json())
    .then(callback)
    .catch(callback);
}

export function fetchFormData(url, callback, data) {
  fetch(url, {
    method: "POST",
    headers: {
      mode: "no-cors",
    },
    body: data,
  })
    .then((response) => response.json())
    .then(callback)
    .catch(callback);
}

export function fetchGETData(url, callback) {
  fetch(url, {
    method: "GET",
    headers: {
      mode: "no-cors",
      Accept: "application/json",
      "Content-Type": "application/json",
    },
  })
    .then((response) => response.json())
    .then(callback)
    .catch(callback);
}
