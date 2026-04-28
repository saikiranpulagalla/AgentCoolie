import React, { ReactNode, ErrorInfo } from 'react';
import { AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
    window.location.href = '/';
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-background p-4">
          <div className="max-w-md w-full space-y-4">
            <div className="flex justify-center">
              <AlertCircle className="h-12 w-12 text-destructive" />
            </div>
            <div className="text-center space-y-2">
              <h1 className="text-2xl font-bold">Something went wrong</h1>
              <p className="text-muted-foreground">
                An unexpected error occurred. Please try again.
              </p>
              {process.env.NODE_ENV === 'development' && this.state.error && (
                <details className="mt-4 p-3 bg-muted rounded text-left text-sm">
                  <summary className="cursor-pointer font-mono font-semibold">
                    Error details (development only)
                  </summary>
                  <pre className="mt-2 overflow-auto text-xs whitespace-pre-wrap break-words">
                    {this.state.error.toString()}
                  </pre>
                </details>
              )}
            </div>
            <Button onClick={this.handleReset} className="w-full">
              Go to Home
            </Button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
