import React from "react";
import Button from "./ui/Button";

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("ErrorBoundary caught an unhandled render error:", error, errorInfo);
    this.setState({ errorInfo });
  }

  handleReload = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-[50vh] flex items-center justify-center p-6">
          <div className="bg-brand-paper border border-brand-line rounded-3xl p-8 max-w-lg w-full text-center shadow-sm space-y-5">
            <div className="w-14 h-14 bg-band-weak/15 text-band-weak rounded-2xl flex items-center justify-center text-2xl mx-auto">
              ⚠️
            </div>
            <div className="space-y-2">
              <h2 className="font-serif text-2xl font-bold text-brand-ink">
                Something went wrong
              </h2>
              <p className="text-sm text-brand-muted">
                An unexpected interface error occurred while rendering this page.
              </p>
            </div>

            <div className="pt-2">
              <Button
                variant="primary"
                onClick={this.handleReload}
                className="w-full sm:w-auto"
              >
                Try refreshing
              </Button>
            </div>

            {this.state.error && (
              <details className="mt-4 text-left border-t border-brand-line pt-4">
                <summary className="text-xs uppercase tracking-wider text-brand-muted cursor-pointer hover:text-brand-ink select-none font-medium">
                  View error details
                </summary>
                <pre className="mt-2 p-3 bg-brand-ivory/60 rounded-xl text-xs font-mono text-brand-ink overflow-x-auto whitespace-pre-wrap max-h-48">
                  {this.state.error.toString()}
                  {this.state.errorInfo?.componentStack}
                </pre>
              </details>
            )}
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
